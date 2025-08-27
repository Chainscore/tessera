from typing import Callable, Final

import asyncio
import signal
import logging
import os
import time
from dotenv import load_dotenv

from jam.logging import setup_logging
from jam.utils.chainspec import chain_config
from .state_update import update_state

from jam.finality.finality import Finality
from jam.settings import setup_setting
from jam.network.start import start_node
from jam.state.state import setup_state
from jam.block import Block

from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.logging import get_logger
from jam.operations.ticket_queue import setup_ticket_queue

# Logger for Node test
logger = get_logger("test")

async def run_node(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
    node_tasks
):
    """Main fn to start the node"""
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) / SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

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
        min_level=getattr(logging, log_level.upper()) if log_level else None
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(name=name, port=int(port), seed=int(seed), data_path="data/")

    main_db = settings.main_db

    logger.info(
        "Starting JAM node",
        name=name,
        port=port,
        ts=init_ts,
        epoch=init_ep,
        spec=chain_config.name,
        environment=environment,
        is_builder=is_builder,
        is_validator=is_validator
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")

        # This fucks up syncing with polkajam, update this elsewhere
        # update_state(state)

        settings.update()
        update_state(state)

        # setup ticket queue
        setup_ticket_queue()

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        settings.update()

        async with asyncio.TaskGroup() as tg:
            tg.create_task(start_node(host, int(port)))
            for node_task in node_tasks:
                if node_task:
                    tg.create_task(node_task())

    except Exception as e:
        logger.critical(
            "JAM node fatal error",
            node_name=name,
            port=port,
            error=str(e)[:200],
            error_type=type(e).__name__
        )

        # Close db connections
        settings.clear()

        raise

def run_node_process(
        genesis_path: str,
        env: str,
        start_genesis: bool,
        theme: str,
        is_builder: bool,
        is_validator: bool,
        node_tasks
):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_node(
        genesis_path,
        env,
        start_genesis,
        theme,
        is_builder,
        is_validator,
        node_tasks
    ))


