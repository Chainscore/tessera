import os
import json
import signal
import asyncio
import structlog
import traceback

from typing import Optional, TYPE_CHECKING

from jam.api.rpc.handlers import SubscriptionPublisher
from jam.api.rpc.service import RPCService
from jam.audit.audit_engine import AuditEngine
from jam.settings import Settings
from jam.state.state import State
from jam.state.storage import StateRecord, StateStorage
from jam.settings import setup_setting
from jam.log_setup import setup_logging
from jam.block.block_view import BlockView
from jam.network.service import NetworkService
from jam.finality.service import FinalityService
from jam.operations.service import OperatorService

from jam.block.block import Block
from jam.block.extrinsics.pool import ExtrinsicPool
from jam.telemetry import TelemetryConfig, TelemetryClient
from jam.utils.chainspec import chain_config

if TYPE_CHECKING:
    from jam.config import NodeConfig


class JamNode:
    """
    Main container class for the Jam Node application.
    Orchestrates startup, shutdown, and service management.
    """

    def __init__(self, config: "NodeConfig"):
        # Initialize NodeConfig
        # This triggers your env-loading and validation logic
        setup_logging(theme=config.LOG_THEME, node_name=config.NODE_NAME)
        self.logger = structlog.get_logger("node")
        self.config = config

        # Triggers
        self.shutdown_event = asyncio.Event()

        # Core Components
        self._settings = None  # Node Settings
        self._state: Optional[State] = None  # Finalized Chain State
        self._ledger: Optional[BlockView] = None  # Chain History (Block View)
        self._pool: ExtrinsicPool = ExtrinsicPool()  # Extrinsic Collection Pool

        # Services
        self.telemetry = None  # Telemetry client
        self._responder: Optional[RPCService] = None  # RPC
        self._grandpa: Optional[FinalityService] = None  # Finality Module
        self._router: Optional[NetworkService] = None  # Networking Module
        self._operator: Optional[OperatorService] = None  # Node Operations Module
        self._auditor: Optional[AuditEngine] = None  # Auditing Module

        # TaskGroup child tasks — tracked for cancellation on shutdown
        self._tg_tasks: list[asyncio.Task] = []


    @property
    def state(self) -> "State":
        if self._state is None:
            raise RuntimeError("Node State is not initialized yet!")
        return self._state

    @state.setter
    def state(self, value: "State") -> None:
        self._state = value

    @property
    def settings(self) -> "Settings":
        if self._settings is None:
            raise RuntimeError("Node Settings is not initialized yet!")
        return self._settings

    @property
    def ledger(self) -> "BlockView":
        if self._ledger is None:
            raise RuntimeError("Block View is not initialized yet!")
        return self._ledger

    @property
    def pool(self) -> "ExtrinsicPool":
        return self._pool

    @property
    def responder(self) -> "RPCService":
        if self._responder is None:
            raise RuntimeError("RPC Service is not initialized yet!")
        return self._responder

    @property
    def publisher(self) -> "SubscriptionPublisher":
        return self.responder.publisher

    @property
    def grandpa(self) -> "FinalityService":
        if self._grandpa is None:
            raise RuntimeError("Finality Service is not initialized yet!")
        return self._grandpa

    @property
    def router(self) -> "NetworkService":
        if self._router is None:
            raise RuntimeError("QUIC Node is not initialized yet!")
        return self._router

    @property
    def operator(self) -> "OperatorService":
        if self._operator is None:
            raise RuntimeError("Operator is not initialized yet!")
        return self._operator

    @property
    def auditor(self) -> "AuditEngine":
        if self._auditor is None:
            raise RuntimeError("Auditor is not initialized yet!")
        return self._auditor

    @property
    def is_rpc_enabled(self):
        return self.config.RPC_FLAG

    @property
    def is_operator_enabled(self):
        # TODO: Handle config flags
        return True

    @property
    def is_telemetry_enabled(self):
        return self.config.TELEMETRY is not None

    def _replay_state(self, state: State, target_block: Block, db) -> None:
        """Replay state updates from genesis to target block to restore Trie."""
        self.logger.info(f"Replaying state to block {target_block.header.slot}...")
        path = []
        curr = target_block
        while curr.header.slot > 0:
            path.append(curr)
            if curr.header.parent == bytes(32):
                break
            curr = Block.load(curr.header.parent, db)
            if not curr:
                self.logger.error(
                    f"Broken chain at slot {path[-1].header.slot}, cannot replay state."
                )
                return

        path.reverse()

        count = 0
        for block in path:
            key = StateStorage.get_storage_key(block.header.hash())
            data = db.get(key)
            if data:
                record = StateRecord.decode(data)
                updates = {}
                deletes = []
                for k, u in record.updates.items():
                    v = u.curr
                    if v == bytes(0) or len(v) == 0:
                        deletes.append(k)
                    else:
                        updates[k] = v

                if updates:
                    state.trie.batch_update(updates)
                for k in deletes:
                    state.trie.delete(k)
                count += 1
            else:
                self.logger.warning(f"Missing state record for block {block.header.slot}")

        self.logger.info(f"Replayed {count} blocks. Trie root: {state.trie.root_hash.hex()}")

    async def rpc_shutdown_trigger(self):
        """Wait for shutdown signal to stop RPC"""
        await self.shutdown_event.wait()

    def handle_exception(self, loop, context):
        exception = context.get("exception")
        message = context.get("message", "")

        # Skip "Future exception was never retrieved" for ConnectionError during cleanup
        if message == "Future exception was never retrieved" and isinstance(
            exception, ConnectionError
        ):
            return

        if isinstance(exception, asyncio.CancelledError):
            self.logger.debug(f"Task cancelled: {message}")
            return

        if exception:
            self.logger.error(
                f"Caught exception: {exception!r}",
                exc_info=(type(exception), exception, exception.__traceback__),
            )
        else:
            self.logger.error(f"Caught exception: {message}")

        if not isinstance(exception, (ConnectionError, asyncio.TimeoutError, OSError)):
            asyncio.create_task(self.graceful_shutdown())

    async def graceful_shutdown(self):
        """Shutdown all services gracefully."""
        if self.shutdown_event.is_set():
            return

        self.logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()

        # 1. Stop operator — cancels run_loop + all tracked dispatch sub-tasks
        if self._operator:
            await self._operator.stop()

        # 2. Stop network — sends sayonara to peers, closes QUIC transport
        if self._router:
            self._router.stop()

        # 3. Cancel TaskGroup child tasks (forces Quart/RPC to stop)
        for task in self._tg_tasks:
            if not task.done():
                task.cancel()

        # 4. Cancel remaining orphaned tasks (protocol handlers, delayed finalization, etc.)
        current = asyncio.current_task()
        pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
        for t in pending:
            t.cancel()

        # Give tasks a moment to run their finally: cleanup blocks
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

        # 5. Close DBs — safe now, no tasks are writing
        if self._settings:
            self._settings.clear()

        self.logger.info("Shutdown complete.")

    def init_services(self):
        # ---------- SETUP TELEMETRY (optional) ----------
        if self.is_telemetry_enabled:
            try:
                telemetry_host, telemetry_port_str = self.config.TELEMETRY.split(":")
                telemetry_port = int(telemetry_port_str)
                telemetry_config = TelemetryConfig(
                    host=telemetry_host, port=telemetry_port, node_name=self.config.NODE_NAME
                )
                self.telemetry = TelemetryClient.setup(telemetry_config)
                self.logger.info(f"Telemetry enabled: {telemetry_host}:{telemetry_port}")
            except Exception as e:
                self.logger.error(f"Failed to setup telemetry: {e}")

        # ---------- SETUP SETTINGS ----------
        # TODO: Settings extended from config?
        self._settings = setup_setting(self.config)

        # ---------- INITIALIZE CORE LOGIC ----------
        self._responder = RPCService(self)
        self._ledger = BlockView(self)
        self._grandpa = FinalityService(self)

        # Initializes Block View
        self._ledger.initialize()

        # Initialize Services
        self._router = NetworkService(self)
        self._operator = OperatorService(self)



    async def start(self) -> None:
        logger = self.logger

        # Initialize Services
        self.init_services()

        logger.info(
            f"Starting Tessera Node! "
            f"name={self.config.NODE_NAME} "
            f"port={self.config.PORT} "
            f"spec={chain_config.name}"
            + (f" rpc_port={self.config.RPC_PORT}" if self.config.RPC_FLAG else "")
        )

        # TODO: Remove Vectors recording later.
        # Enable vector recording if JAM_VECTOR_RECORD env var is set  # VECTOR
        _vec_cycle = os.environ.get("JAM_VECTOR_RECORD", "")  # VECTOR
        if _vec_cycle:  # VECTOR
            from jam.vectors import recorder as vec  # VECTOR
            vec.enable(_vec_cycle)  # VECTOR

        main_db = self.settings.main_db
        state_db = self.settings.state_db

        try:
            # Set up custom exception handler for the event loop
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(self.handle_exception)

            # Register signal handlers for graceful shutdown on SIGTERM/SIGINT
            # First Ctrl+C warns, second Ctrl+C actually shuts down
            self._sigint_count = 0

            def _handle_signal():
                print()  # newline after ^C so logs start on a fresh line
                self._sigint_count += 1
                if self._sigint_count == 1:
                    print("\033[1;91m ⚠  Interrupt received. Press Ctrl+C again to shut down.\033[0m")
                else:
                    asyncio.create_task(self.graceful_shutdown())

            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    loop.add_signal_handler(sig, _handle_signal)
                except NotImplementedError:
                    pass

            # -------------- SETUP STATE -------------
            # Set genesis state
            # We need to adapt setup_state to return state instance instead of setting global
            if os.path.exists("dev-spec.json"):
                with open("dev-spec.json") as f:
                    dev_spec = json.load(f)

                from tsrkit_types import Dictionary, Bytes

                logger.info("Setting up state from genesis: dev-spec.json")
                genesis_json = json.load(open("dev-spec.json"))
                data = Dictionary[Bytes, Bytes].from_json(genesis_json["genesis_state"])

                self.state = State.from_keyvals(data, self)
                self.state.store.enable_writes()
                self.state.store.enable_cache()

                # Check if we need to restore state from DB.
                # TEST: State progression from DB itself.
                final_blk = self.grandpa.load_final()
                if final_blk and final_blk.header.slot > 0:
                    self._replay_state(self.state, final_blk, main_db)

            else:
                logger.warning("dev-spec.json not found, skipping genesis state setup")
                # Fallback or load from DB if existing?
                # If DB exists, we should load from it.
                # This logic is a bit naive in original code too.
                # Just keeping "pass" for now to match behavior, but self.state might be None!

                # TODO: May be request keyvals directly from other node? Or maybe load state from db?
                key_vals = state_db.get_all()
                self.state = State.from_keyvals(key_vals, self)


            # Update Operator with State
            # self.operator.state = self.state

            # ------------ SET GENESIS BLOCK ------------
            if "dev_spec" in locals():
                block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
                # Block save logic needs DB
                block.save(main_db)

                self.grandpa.set_head(block)
                self.grandpa.finalise(block, initial=True)

                if self.telemetry:
                    self.telemetry.set_node_identity(
                        self.settings.ed25519_public, block.header.hash()
                    )

            # ----------- START NODE --------------
            async with asyncio.TaskGroup() as tg:
                # Telemetry
                if self.telemetry:
                    tg.create_task(self.telemetry.run())

                # Network Service
                self._tg_tasks.append(tg.create_task(self.router.start()))

                # RPC
                if self.is_rpc_enabled:
                    self._tg_tasks.append(tg.create_task(self.responder.start()))

                # Operator Service
                if self.is_operator_enabled:
                    self._tg_tasks.append(tg.create_task(self.operator.start()))

                # Connect to peers (after network start)
                await asyncio.sleep(2)

                if self.state:
                    self._tg_tasks.append(tg.create_task(self.router.connect_to_peers()))

        except asyncio.CancelledError:
            # Normal shutdown path — TaskGroup children were cancelled by graceful_shutdown
            logger.info("Tessera node folded. Until next block, sayonara!")
        except ExceptionGroup as eg:
            self.shutdown_event.set()
            logger.critical(f"Fatal error: {eg} ({type(eg).__name__})")
            for i, exc in enumerate(eg.exceptions):
                tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                logger.critical(f"Sub-exception {i + 1}: {type(exc).__name__}: {exc}\n{tb_str}")
            await self.graceful_shutdown()
        except Exception as e:
            self.shutdown_event.set()
            tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.critical(f"Fatal error: {e} ({type(e).__name__})\n{tb_str}")
            await self.graceful_shutdown()
        finally:
            self.shutdown_event.set()
