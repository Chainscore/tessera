import asyncio
import json
import logging
import os
import time
from dotenv import load_dotenv

from jam.finality.finality import Finality
from jam.logging import setup_logging, logger
from jam.network.start import start_node
from jam.operations.operator import operate
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting
from jam.network.node import Node
from jam.state.state import setup_state
from jam.block import Block
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH
from jam.api.rpc.app import rpc
from hypercorn.asyncio import serve
from hypercorn.config import Config
from jam.api.rpc.app import rpc
from jam.operations.ticket_queue import setup_ticket_queue


async def main(
    genesis_path: str,
    env: str,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    if not is_builder and not is_validator:
        is_validator=True
    # ---------- LOAD ENVIRONMENT ----------
    # load_dotenv(".env")
    # load_dotenv(env,override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]
    host = os.environ["HOST"]

    if not name or not port or not host or not seed:
        raise ValueError(f"Missing node info in {env}")

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
        name=name, port=int(port), seed=int(seed), data_path="data/"
    )

    main_db = settings.main_db

    logger.info(
        "Starting Jam Node!",
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
    )

    try:
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open(genesis_path))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, genesis_path)
        state.store.disable_cache()

        # FIX: setup ticket queue
        setup_ticket_queue()

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        # RPC/WebSocket server setup
        rpc_port = int(os.environ.get("RPC_PORT", 5000))
        rpc_config = Config()
        rpc_config.bind = [f"{host}:{port}"]
        rpc_config.debug = True
        rpc_config.use_reloader = False

        logger.info("📡 Starting RPC/WebSocket server", host=host, port=rpc_port)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(start_node(str(host), int(port), is_builder))
            # RPC
            # tg.create_task(rpc.run_task(debug=True, host="0.0.0.0", port=5001))
            # Node Ops - Block Prod, Audit, Assurances, etc
            tg.create_task(operate(is_builder))

    except Exception as e:
        logger.critical("Fatal error", e=e, error_type=type(e).__name__)
        # Close db connections
        settings.clear()
