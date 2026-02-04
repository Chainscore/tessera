import asyncio
import math
import time
from typing import List, Tuple, Type, cast, Optional

from jam.log_setup import node_logger as logger
from jam.utils.task_utils import create_safe_task
from jam.operations.handlers import WPBuilder, assurer, BlockProducer, Conductor, Forwarding
from jam.operations.dispatcher import NodeDispatcher
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, TICKET_SUBMISSION_END
from jam.finality.finality import Finality
from jam.network.service import NetworkService
from jam.config import NodeConfig

from jam.state.state import State

class OperatorService:
    def __init__(self, config: NodeConfig, network_service: NetworkService, settings):
        self.config = config
        self.network_service = network_service
        self.settings = settings
        self.state: Optional[State] = None
        self._running = False
        self._task = None
        self._initial_connection_made = False

    def dispatch_fns(self) -> List[Tuple[int, Type[NodeDispatcher] | None]]:
        return [
            (0, BlockProducer),
            (2, None),  # audit
            (4, cast(Type[NodeDispatcher], assurer)),  # transmit assurances
        ]

    async def schedule_run(self, sch_ts: int, runner: Type[NodeDispatcher], *args) -> None:
        await asyncio.sleep(sch_ts)
        # Note: We might need to pass dependencies to runners if they were relying on globals
        await runner.run(*args)

    async def run_loop(self):
        """
        Starts a never ending 6-sec loop
        """
        curr_time = time.time()
        ts = math.ceil((curr_time - GENESIS_TS) / 6)
        conductor_ts = max((EPOCH_LENGTH // 60), 1)
        forwarding_s = max((EPOCH_LENGTH // 20), 1)
        ticket_generated = False
        self._running = True

        while self._running:
            try:
                # If we not yet in ts timeslot, sleep for a while
                ts_start_time = GENESIS_TS + ts * 6
                curr_time = time.time()
                if curr_time < ts_start_time:
                    await asyncio.sleep(ts_start_time - curr_time)

                # Check if network is ready
                if not self.network_service.node:
                    ts += 1
                    await asyncio.sleep(0.1)
                    continue

                active_peers = len(self.network_service.node.active_peers)
                connections = len(self.network_service.node.all_connected)
                logger.debug(f"New Time Slot #{ts}", slot_index=(ts % EPOCH_LENGTH), epoch=int(ts // EPOCH_LENGTH), peers=active_peers, connections=connections)

                # Schedule tasks to run immediately
                main_db = self.settings.main_db
                finality_block = Finality.load_final(main_db)
                finality_time_slot = finality_block.header.slot

                if conductor_ts <= (finality_time_slot%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2) and not ticket_generated:
                    if self.state and self.network_service.node:
                        create_safe_task(self.schedule_run(0, Conductor, ts, finality_time_slot, self.state, self.network_service.node), name="conductor")
                        ticket_generated = True

                if forwarding_s <= (finality_time_slot%EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2):
                    create_safe_task(self.schedule_run(0, Forwarding, finality_time_slot%EPOCH_LENGTH, finality_time_slot), name="forwarding")

                for dispatch in self.dispatch_fns():
                    (task_ts, runner) = dispatch
                    if not runner:
                        continue

                    # Get name from class or instance
                    runner_name = getattr(runner, '__name__', type(runner).__name__)
                    
                    if runner == BlockProducer:
                        if self.state and self.network_service.node and self.state.finality_service:
                            create_safe_task(
                                self.schedule_run(
                                    task_ts, 
                                    runner, 
                                    ts, 
                                    self.state, 
                                    self.settings, 
                                    self.network_service.node, 
                                    self.state.finality_service
                                ), 
                                name=f"dispatch_{runner_name}"
                            )
                    elif isinstance(runner, type(assurer)): # check if it is Assurer instance
                         create_safe_task(self.schedule_run(task_ts, runner, ts, self.state, self.settings), name=f"dispatch_{runner_name}")
                    else:
                        create_safe_task(self.schedule_run(task_ts, runner, ts), name=f"dispatch_{runner_name}")

                if ts%EPOCH_LENGTH == 11:
                    ticket_generated = False
                    # TODO: Inject these dependencies instead of inline import if possible, 
                    # but they are likely singletons/globals in their own modules.
                    from jam.block.extrinsics.disputes import dpt_store
                    from jam.block.extrinsics.tickets import ticket_store
                    ticket_store.clear()
                    dpt_store.clear()

                if ts%EPOCH_LENGTH == 0 or not self._initial_connection_made:
                    self.settings.update(self.state)
                    if self.state and self.network_service.node:
                        create_safe_task(self.network_service.connect_to_peers(self.state, self.settings), name="connect_peers")
                        self._initial_connection_made = True

            except asyncio.CancelledError:
                self._running = False
                break
            except Exception as e:
                logger.error(f"Error in operate loop", error=str(e), exc_info=True, time_slot=ts)

            # Move on to next timeslot and sleep
            ts += 1

    async def start(self):
        self._task = asyncio.create_task(self.run_loop())
        return self._task

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
