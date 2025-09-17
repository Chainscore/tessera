import pytest
import asyncio
import logging
import signal
import os
import time
from multiprocessing import Process
from jam.network.start import start_node as start_global_node

from dotenv import load_dotenv

from jam.log_setup import setup_logging, logger
from jam.utils.chainspec import chain_config

from jam.finality.finality import Finality
from jam.settings import setup_setting

from jam.network.protocols.ce_201 import GhostProtocol

# from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.block import Block

from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD

clients = [40000, 40001]


# DEFINE NODE TASKS
async def start_node():
    # TEMP FIX: Wait for node to initialize
    from jam.network.start import node
    await asyncio.sleep(5)

    for client in node.all_connected:

        protocol = GhostProtocol()
        message = f"Hello {client.port}"

        responses = await protocol.transmit(message)
        expected_message = f"DATA RECEIVED: {message}"

        for response in responses:
            assert response == expected_message


async def run_node(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
):
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
        min_level=getattr(logging, log_level.upper()) if log_level else None,
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
        is_validator=is_validator,
    )

    try:
        # Set genesis state
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, "dev-spec.json")
        state.store.disable_cache()
        # update_state(state)

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(start_global_node(str(host), int(port)))
            tg.create_task(start_node())

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
):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_node(genesis_path, env, start_genesis, theme, is_builder, is_validator))


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_connection():
    tasks = []

    p_alice = Process(
        target=run_node_process, args=("", "envs/40000.env", True, "matrix", False, True)
    )
    p_bob = Process(
        target=run_node_process, args=("", "envs/40001.env", True, "polkadot", False, True)
    )

    p_alice.start()
    p_bob.start()

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(20)

    print("END OF TEST")

    p_alice.terminate()
    p_bob.terminate()
    p_alice.join()
    p_bob.join()
