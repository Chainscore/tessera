from pathlib import Path
import shutil
import asyncio
import signal
import os
from dotenv import load_dotenv

from jam.log_setup import setup_logging, logger
from jam.utils.chainspec import chain_config

from jam.jam_node import JamNode
from jam.config import NodeConfig

# Legacy imports check
try:
    from jam.operations import operate
except ImportError:
    operate = None

shutdown_event = asyncio.Event()

async def run_node(
    db: str,
    env: str,
    theme: str,
    is_builder: bool,
    is_validator: bool,
    node_tasks,
    rpc_flag: bool
) -> None:

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

    # Use NodeConfig to parse environment
    # We might need to manually set some overrides if they aren't in env vars 
    # but passed via args to this function.
    # run_node args: db, env (path), theme, is_builder, is_validator, node_tasks, rpc_flag
    
    overrides = {}
    if db:
        overrides["DATA_PATH"] = db
    if theme:
        overrides["LOG_THEME"] = theme
    if rpc_flag is not None:
        overrides["RPC_FLAG"] = rpc_flag
    if is_builder:
        overrides["BUILDER"] = True
    if is_validator:
        overrides["VALIDATOR"] = True
        
    # We also need to handle NODE_NAME, PORT, SEED, HOST, RPC_HOST, RPC_PORT from env
    # NodeConfig should handle this if env_file is passed.
    
    try:
        config = NodeConfig(_env_file=env, **overrides)
        
        # Manually ensure some things that might fall through if .env loading is weird in tests
        # The original run_node explicitly got them from os.environ after load_dotenv
        if not config.NODE_NAME or not config.PORT or not config.SEED:
             # Just in case NodeConfig didn't pick up correctly from the env file argument?
             # NodeConfig uses pydantic-settings which should handle _env_file.
             pass

        setup_logging(theme=config.LOG_THEME, node_name=config.NODE_NAME)
        
        node = JamNode(config)
        
        # Handle node tasks
        # If 'operate' is in node_tasks, we skip it because JamNode runs OperatorService
        extra_tasks = []
        if node_tasks:
            for task in node_tasks:
                task_name = getattr(task, '__name__', str(task))
                if task_name == 'operate':
                    continue
                # For other tasks like node_info_printer, we might have issues if they rely on globals
                # We will try to run them, but they might fail if they import 'jam.network.start.node'
                extra_tasks.append(task)

        if extra_tasks:
            logger.info(f"Running extra tasks: {[t.__name__ for t in extra_tasks]}")

        # Clean start
        if config.RPC_FLAG:
            logger.info(f"Starting Tessera Node (Test)! name={config.NODE_NAME} port={config.PORT} spec={chain_config.name} rpc_port={config.RPC_PORT}")
        else:
            logger.info(f"Starting Tessera Node (Test)! name={config.NODE_NAME} port={config.PORT} spec={chain_config.name}")

        async with asyncio.TaskGroup() as tg:
            tg.create_task(node.start())
            
            for task in extra_tasks:
                # These tasks usually expect no args or depend on globals
                tg.create_task(task())
            
            # Wait for shutdown event? 
            # JamNode.start() runs until shutdown.
            pass

    except asyncio.exceptions.CancelledError:
        logger.info("Node cancelled")
        await node.graceful_shutdown()
        raise
    except Exception as e:
        logger.critical(f"Fatal error in run_node: {e}", exc_info=True)
        # Cleanup
        if Path("data/tmp").exists():
            shutil.rmtree("data/tmp")
        if 'node' in locals() and node.settings:
            node.settings.clear()
        raise

def run_node_process(
        db: str,
        env: str,
        start_genesis: bool,
        theme: str,
        is_builder: bool,
        is_validator: bool,
        node_tasks,
        rpc_flag: bool
):
    try:
        # Handle clean termination
        def handle_sigterm(signum, frame):
            exit(0)

        signal.signal(signal.SIGTERM, handle_sigterm)

        asyncio.run(run_node(
            db,
            env,
            theme,
            is_builder,
            is_validator,
            node_tasks,
            rpc_flag
        ))
    except asyncio.exceptions.CancelledError:
        asyncio.Runner().close()
        print("\nCtrl-C received, Node shutting down!!!!!!")
