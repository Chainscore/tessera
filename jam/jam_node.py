import asyncio
import json
import logging
import os
import shutil
import traceback
import signal
from pathlib import Path
from typing import Optional

from jam.config import NodeConfig
from jam.settings import setup_setting
from jam.log_setup import setup_logging, logger
from jam.block.block_view import BlockView
from jam.finality.service import FinalityService
from jam.state.state import State
from jam.state.storage import StateRecord, StateStorage
from jam.operations.ticket_queue import setup_ticket_queue
from jam.network.service import NetworkService
from jam.operations.service import OperatorService
from jam.utils.chainspec import chain_config
from jam.block.block import Block
from jam.api.rpc.app import rpc

class JamNode:
    """
    Main container class for the Jam Node application.
    Orchestrates startup, shutdown, and service management.
    """
    def __init__(self, config: NodeConfig):
        self.config = config
        self.shutdown_event = asyncio.Event()
        self.settings = None
        self.telemetry_client = None
        
        # Core Components
        self.block_view: Optional[BlockView] = None
        self.finality_service: Optional[FinalityService] = None
        self.state: Optional[State] = None
        
        # Services
        self._network_service: Optional[NetworkService] = None
        self._operator_service: Optional[OperatorService] = None

    def _replay_state(self, state: State, target_block: Block, db) -> None:
        """Replay state updates from genesis to target block to restore Trie."""
        logger.info(f"Replaying state to block {target_block.header.slot}...")
        path = []
        curr = target_block
        while curr.header.slot > 0:
            path.append(curr)
            if curr.header.parent == bytes(32):
                break
            curr = Block.load(curr.header.parent, db)
            if not curr:
                logger.error(f"Broken chain at slot {path[-1].header.slot}, cannot replay state.")
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
                     state.store._TRIE.batch_update(updates)
                 for k in deletes:
                     state.store._TRIE.delete(k)
                 count += 1
            else:
                 logger.warning(f"Missing state record for block {block.header.slot}")
        
        logger.info(f"Replayed {count} blocks. Trie root: {state.store._TRIE.root_hash.hex()}")

    async def rpc_shutdown_trigger(self):
        """Wait for shutdown signal to stop RPC"""
        await self.shutdown_event.wait()

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        logger.error(f"Caught exception: {msg}")
        # trigger shutdown
        asyncio.create_task(self.graceful_shutdown())

    async def graceful_shutdown(self):
        """Shutdown all services gracefully."""
        if self.shutdown_event.is_set() and not self._operator_service: # already shutting down or not started
             # If we are already shutting down, just return? 
             # But we need to ensure services stop.
             pass

        logger.info("Initiating graceful shutdown...")
        self.shutdown_event.set()

        # Stop services
        if self._operator_service:
            await self._operator_service.stop()
        
        if self._network_service:
            self._network_service.stop()
            # Give time for socket to close
            await asyncio.sleep(0.5)
            
        # Close DBs
        if self.settings:
            self.settings.clear()
            
        logger.info("Shutdown complete.")

    async def start(self) -> None:
        # Note: Logging should be set up before calling start() usually
        # setup_logging(theme=self.config.LOG_THEME, node_name=self.config.NODE_NAME)

        # ---------- SETUP TELEMETRY (optional) ----------
        if self.config.TELEMETRY:
            try:
                telemetry_host, telemetry_port_str = self.config.TELEMETRY.split(":")
                telemetry_port = int(telemetry_port_str)
                telemetry_config = TelemetryConfig(
                    host=telemetry_host, 
                    port=telemetry_port, 
                    node_name=self.config.NODE_NAME
                )
                self.telemetry_client = TelemetryClient.setup(telemetry_config)
                logger.info(f"Telemetry enabled: {telemetry_host}:{telemetry_port}")
            except Exception as e:
                logger.error(f"Failed to setup telemetry: {e}")

        # ---------- SETUP SETTINGS ----------
        self.settings = setup_setting(
            name=self.config.NODE_NAME, 
            port=self.config.PORT, 
            seed=int(self.config.SEED), 
            data_path=self.config.DATA_PATH, 
            rpc_flag=self.config.RPC_FLAG
        )

        main_db = self.settings.main_db
        state_db = self.settings.state_db
        
        # ---------- INITIALIZE CORE LOGIC ----------
        self.block_view = BlockView()
        self.finality_service = FinalityService(self.block_view, main_db)
        
        # Initializes Block View
        self.block_view.initialize(main_db)

        # Initialize Services
        self._network_service = NetworkService(self.config)
        self._operator_service = OperatorService(
            self.config, 
            self._network_service, 
            self.settings,
            # We need to pass State but it's not ready yet. 
            # We can pass the JamNode itself or set it later?
            # Or OperatorService gets state via a property/method.
            # Ideally OperatorService is initialized AFTER state.
        )
        
        if self.config.RPC_FLAG:
            logger.info(
                f"Starting Tessera Node! name={self.config.NODE_NAME} port={self.config.PORT} "
                f"spec={chain_config.name} rpc_port={self.config.RPC_PORT}"
            )
        else:
            logger.info(
                f"Starting Tessera Node! name={self.config.NODE_NAME} port={self.config.PORT} "
                f"spec={chain_config.name}"
            )

        try:
            # Set up custom exception handler for the event loop
            loop = asyncio.get_running_loop()
            loop.set_exception_handler(self.handle_exception)

            # Register signal handlers for graceful shutdown on SIGTERM/SIGINT
            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    loop.add_signal_handler(sig, lambda: asyncio.create_task(self.graceful_shutdown()))
                except NotImplementedError:
                    pass

            # -------------- SETUP STATE -------------
            # Set genesis state
            # We need to adapt setup_state to return state instance instead of setting global
            if os.path.exists("dev-spec.json"):
                with open("dev-spec.json") as f:
                    dev_spec = json.load(f)
                
                # Logic from old setup_state, refactored here or imported
                # For now using imported logic but modifying it to not use global 'state'
                # Actually, State.from_keyvals is cleaner.
                
                # We need to construct genesis data logic here or in a helper
                # Let's use a helper in jam_node or inline if simple
                
                # ... (Genesis loading logic) ...
                # Assuming setup_state returns a State instance now (we need to modify setup_state in state.py or here)
                # Let's assume we modify jam/state/state.py's setup_state to accept finality_service and return state
                # Wait, I didn't verify setup_state modification in previous step.
                
                from jam.state.state import GhostState
                from tsrkit_types import Dictionary, Bytes
                
                logger.info("Setting up state from genesis: dev-spec.json")
                genesis_json = json.load(open("dev-spec.json"))
                data = Dictionary[Bytes, Bytes].from_json(genesis_json["genesis_state"])
                
                self.state = State.from_keyvals(data, state_db, self.finality_service, self.settings)
                self.state.store.enable_writes()
                self.state.store.enable_cache()

                # Check if we need to restore state from DB
                final_blk = self.finality_service.load_final()
                if final_blk and final_blk.header.slot > 0:
                     self._replay_state(self.state, final_blk, main_db)
                
            else:
                logger.warning("dev-spec.json not found, skipping genesis state setup")
                # Fallback or load from DB if existing?
                # If DB exists, we should load from it. 
                # This logic is a bit naive in original code too.
                # Just keeping "pass" for now to match behavior, but self.state might be None!
                self.state = State(None, self.finality_service, self.settings) # Empty state??
            
            # Update Operator with State
            self._operator_service.state = self.state
            
            # Update global state for legacy support
            import jam.state.state
            jam.state.state.state = self.state
            
            # Setup Ticket Queue
            setup_ticket_queue()

            # ------------ SET GENESIS BLOCK ------------
            if 'dev_spec' in locals():
                block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
                # Block save logic needs DB
                block.save(main_db)
                
                self.finality_service.set_head(block)
                self.finality_service.finalise(block, initial=True)

                if self.telemetry_client:
                    self.telemetry_client.set_node_identity(self.settings.ed25519_public, block.header.hash())

            # ----------- START NODE --------------
            async with asyncio.TaskGroup() as tg:
                # Telemetry
                if self.telemetry_client:
                    tg.create_task(self.telemetry_client.run())
                
                # Network Service
                # Network might need state? 
                # connect_to_peers needs state.
                tg.create_task(self._network_service.start())
                
                # RPC
                if self.config.RPC_FLAG:
                    tg.create_task(
                        rpc.run_task(
                            debug=True,
                            host=self.config.RPC_HOST,
                            port=int(self.config.RPC_PORT),
                            shutdown_trigger=self.rpc_shutdown_trigger,
                        )
                    )
                
                # Operator Service
                tg.create_task(self._operator_service.start())
                
                # Connect to peers (after network start)
                if self.state:
                    tg.create_task(self._network_service.connect_to_peers(self.state, self.settings))

        except ExceptionGroup as eg:
            self.shutdown_event.set()
            logger.critical(f"Fatal error: {eg} ({type(eg).__name__})")
            for i, exc in enumerate(eg.exceptions):
                tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                logger.critical(f"Sub-exception {i + 1}: {type(exc).__name__}: {exc}\n{tb_str}")
            await self.graceful_shutdown()
            raise asyncio.exceptions.CancelledError
        except Exception as e:
            self.shutdown_event.set()
            tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            logger.critical(f"Fatal error: {e} ({type(e).__name__})\n{tb_str}")
            await self.graceful_shutdown()
            raise asyncio.exceptions.CancelledError
        finally:
            self.shutdown_event.set()
