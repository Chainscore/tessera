import os
import time
import signal
import asyncio
import logging

from dotenv import load_dotenv

from jam.block import Block

from jam.finality.finality import Finality
from jam.log_setup import setup_logging, logger


from jam.settings import setup_setting
from jam.state.state import setup_state
from jam.network.start import start_node
from jam.types.protocol.validators import IPAddress

from jam.utils.chainspec import chain_config
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD

from tests.integration.utils.state_update import update_state

async def run_node(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
    node_task,
):
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = (time.time() - genesis_ts) / SLOT_PERIOD
    init_ep = init_ts // EPOCH_LENGTH

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
        min_level=getattr(logging, log_level.upper()) if log_level else None,
    )

    # ---------- SETUP SETTINGS ----------
    settings = setup_setting(
        name=name, port=int(port), seed=int(seed), data_path="data/"
    )

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
        is_validator=is_validator,
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")
        state.store.disable_cache()
        update_state(state)

        settings.update()

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db, True)

        settings.update()

        async with asyncio.TaskGroup() as tg:
            await start_node(host, int(port))
            if node_task:
                print("STARTING NODE TASKS")
                tg.create_task(node_task())

    except KeyboardInterrupt:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="keyboard_interrupt",
        )
    except Exception as e:
        logger.critical(
            "JAM node fatal error",
            node_name=name,
            port=port,
            error=str(e)[:200],
            error_type=type(e).__name__,
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
    node_task,
):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(
        run_node(
            genesis_path, env, start_genesis, theme, is_builder, is_validator, node_task
        )
    )
