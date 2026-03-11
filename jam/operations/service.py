import asyncio
import math
import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from jam.operations import WPBuilder
from jam.utils.task_utils import create_safe_task
from jam.incore.doer import Doer
from jam.operations.handlers.assurer import Assurer
from jam.operations.handlers.bp_engine import BlockProducer
from jam.operations.handlers.conductor import Conductor
from jam.operations.handlers.forwarding import Forwarding
from jam.operations.handlers.monitor import Monitor
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, TICKET_SUBMISSION_END

if TYPE_CHECKING:
    from jam.jam_node import JamNode


@dataclass
class OperatorConfig:
    """Configuration for which operator handlers to initialize."""
    author: bool = True
    assurer: bool = True
    conductor: bool = True
    postman: bool = True
    builder: bool = False
    monitor: bool = True


class OperatorService(Doer):
    def __init__(self, jam: "JamNode", config: Optional[OperatorConfig] = None):
        super().__init__(jam)
        self._running = False
        self._task = None
        self._active_tasks: set[asyncio.Task] = set()
        self._config = config or OperatorConfig()

        # Handler instances
        self._assurer: Optional[Assurer] = Assurer(jam) if self._config.assurer else None
        self._builder: Optional[WPBuilder] = WPBuilder(jam) if self._config.builder else None
        self._author: Optional[BlockProducer] = BlockProducer(jam) if self._config.author else None
        self._conductor: Optional[Conductor] = Conductor(jam) if self._config.conductor else None
        self._postman: Optional[Forwarding] = Forwarding(jam) if self._config.postman else None
        self._monitor: Optional[Monitor] = Monitor(jam) if self._config.monitor else None

    # -- Overrides --

    @property
    def operator(self):
        return self

    @property
    def assurer(self) -> Optional[Assurer]:
        return self._assurer

    @property
    def builder(self) -> Optional[WPBuilder]:
        return self._builder

    @property
    def author(self) -> Optional[BlockProducer]:
        return self._author

    @property
    def conductor(self) -> Optional[Conductor]:
        return self._conductor

    @property
    def postman(self) -> Optional[Forwarding]:
        return self._postman

    # -- Scheduling --

    def _dispatchers(self):
        """Return (offset_seconds, handler) pairs for per-slot tasks."""
        dispatchers = []
        if self._author:
            dispatchers.append((0, self._author))
        if self._assurer:
            dispatchers.append((4, self._assurer))
        if self._monitor:
            dispatchers.append((0, self._monitor))
        return dispatchers

    def _tracked_task(self, coro, name: str = None) -> asyncio.Task:
        """Create a fire-and-forget task that is tracked for shutdown cleanup."""
        task = create_safe_task(coro, name=name)
        self._active_tasks.add(task)
        task.add_done_callback(self._active_tasks.discard)
        return task

    @staticmethod
    async def _schedule_run(delay: float, handler, *args):
        if delay > 0:
            await asyncio.sleep(delay)
        await handler.run(*args)

    async def run_loop(self):
        curr_time = time.time()
        ts = math.ceil((curr_time - GENESIS_TS) / 6)
        conductor_ts = max((EPOCH_LENGTH // 60), 1)
        forwarding_s = max((EPOCH_LENGTH // 20), 1)
        ticket_generated = False
        self._running = True

        while self._running:
            try:
                # Wait until this timeslot starts
                ts_start_time = GENESIS_TS + ts * 6
                curr_time = time.time()
                if curr_time < ts_start_time:
                    await asyncio.sleep(ts_start_time - curr_time)

                state = self.state
                settings = self.settings
                grandpa = self.grandpa

                finality_block = grandpa.load_final()
                finality_time_slot = finality_block.header.slot

                # Conductor: generate tickets at the right epoch window
                if (self._conductor
                        and conductor_ts <= (finality_time_slot % EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2)
                        and not ticket_generated):
                    self._tracked_task(
                        self._schedule_run(0, self._conductor, ts, finality_time_slot),
                        name="conductor",
                    )
                    ticket_generated = True

                # Postman: forward tickets
                if (self._postman
                        and forwarding_s <= (finality_time_slot % EPOCH_LENGTH) < (TICKET_SUBMISSION_END // 2)):
                    self._tracked_task(
                        self._schedule_run(0, self._postman, finality_time_slot % EPOCH_LENGTH, finality_time_slot),
                        name="postman",
                    )

                # Per-slot dispatchers (block producer, assurer)
                for offset, handler in self._dispatchers():
                    name = type(handler).__name__
                    self._tracked_task(
                        self._schedule_run(offset, handler, ts),
                        name=f"dispatch_{name}",
                    )

                # Epoch boundary cleanup
                if ts % EPOCH_LENGTH == 11:
                    ticket_generated = False
                    self.pool.tickets.clear()
                    self.pool.disputes.clear()

                if ts % EPOCH_LENGTH == 0:
                    settings.update(state)

            except asyncio.CancelledError:
                self._running = False
                break
            except Exception as e:
                self.logger.error("Error in operate loop", error=str(e), exc_info=True, time_slot=ts)

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
        # Cancel any in-flight dispatch tasks (block producer, assurer, conductor, etc.)
        for t in list(self._active_tasks):
            if not t.done():
                t.cancel()
        if self._active_tasks:
            await asyncio.gather(*self._active_tasks, return_exceptions=True)
        self._active_tasks.clear()
