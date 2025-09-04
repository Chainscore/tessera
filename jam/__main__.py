import asyncio
import json
import logging
import os
from pathlib import Path
import shutil
from typing import TYPE_CHECKING

# Only import essential modules at startup
from dotenv import load_dotenv

if TYPE_CHECKING:
    from jam.finality.finality import Finality
    from jam.logging import setup_logging
    from jam.network.start import start_node
    from jam.operations.operator import operate
    from jam.utils.chainspec import chain_config
    from jam.settings import setup_setting
    from jam.state.state import setup_state
    from jam.block import Block
    from jam.api.rpc.app import rpc
    from jam.operations.ticket_queue import setup_ticket_queue

# Lazy import functions for heavy modules
def lazy_import_logging():
    from jam.logging import setup_logging, logger
    return setup_logging, logger

def lazy_import_network():
    from jam.network.start import start_node
    return start_node

def lazy_import_operations():
    from jam.operations.operator import operate
    from jam.operations.ticket_queue import setup_ticket_queue
    return operate, setup_ticket_queue

def lazy_import_state():
    from jam.state.state import setup_state
    from jam.settings import setup_setting
    return setup_state, setup_setting

def lazy_import_finality():
    from jam.finality.finality import Finality
    return Finality

def lazy_import_block():
    from jam.block import Block
    return Block

def lazy_import_rpc():
    from jam.api.rpc.app import rpc
    return rpc

def lazy_import_chainspec():
    from jam.utils.chainspec import chain_config
    return chain_config


async def main(
    db: str,
    env: str,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    if not is_builder and not is_validator:
        is_validator=True
    
    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env,override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]
    host = os.environ["HOST"]

    if not name or not port or not host or not seed:
        raise ValueError(f"Missing node info in {env}")

    # ---------- LAZY IMPORTS ----------
    setup_logging, logger = lazy_import_logging()
    setup_state, setup_setting = lazy_import_state()
    chain_config = lazy_import_chainspec()

    # ---------- SETUP LOGGING ----------
    environment = os.environ.get("ENVIRONMENT", "development")
    log_level = os.environ.get("LOG_LEVEL", None)

    setup_logging(
        theme=theme,
        node_name=name,
        environment=environment,
        min_level=getattr(logging, log_level.upper()) if log_level else None,
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(
        name=name, port=int(port), seed=int(seed), data_path=db
    )

    main_db = settings.main_db

    logger.info(
        "Starting Tessera Node!",
        name=name,
        port=port,
        spec=chain_config.name,
    )

    try:
        # -------------- LAZY IMPORTS FOR HEAVY MODULES -------------
        Block = lazy_import_block()
        Finality = lazy_import_finality()
        operate, setup_ticket_queue = lazy_import_operations()
        start_node = lazy_import_network()
        rpc = lazy_import_rpc()
        
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open("dev-spec.json"))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")

        # FIX: setup ticket queue
        setup_ticket_queue()

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        # RPC/WebSocket server setup
        rpc_port = int(os.environ.get("RPC_PORT", 5000))

        logger.info("📡 Starting RPC/WebSocket server", host=host, port=rpc_port)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(start_node(str(host), int(port), is_builder))
            # RPC
            tg.create_task(rpc.run_task(debug=True, host=host, port=rpc_port))
            # Node Ops - Block Prod, Audit, Assurances, etc
            tg.create_task(operate(is_builder))

    except Exception as e:
        logger.critical("Fatal error", e=e, error_type=type(e).__name__)
        # Close db connections
        if Path("data/tmp").exists():
            shutil.rmtree("data/tmp")
        settings.clear()
