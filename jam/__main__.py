import asyncio
import json
import logging
import os
import time

from asyncio import CancelledError
from dotenv import load_dotenv
from jam.operations import operate
from jam.logging import setup_logging, logger
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting
from jam.finality.finality import Finality
from jam.network.peer import Peer
from jam.network.node import setup_node
# from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.block import Block
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH
from tests.integration.utils.state_update import update_state

TIMESLOT = 0

async def main(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)

    global TIMESLOT
    TIMESLOT = init_ts

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

        # TODO: Remove Later
        update_state(state)

        # ----------- SETUP NETWORKING ------------
        peers = [Peer(data=val) for val in state.kappa if val.metadata.port != port]

        tsr_node = setup_node(
            name,
            int(port),
            peers,
            host=str(host),
            is_bd=is_builder,
            is_val=is_validator,
        )

        # ------------ SET GENESIS BLOCK ------------
        block = Block.decode(bytes.fromhex(dev_spec["genesis_header"]))
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)
        Finality.finalise(header_hash, main_db)

        # ----------- START NODE --------------
        async with asyncio.TaskGroup() as tg:
            # Networking - Block Imports, WP Processing, etc
            tg.create_task(tsr_node.initialize())
            # RPC
            # tg.create_task(rpc.run_task(debug=True, host="0.0.0.0", port=5001))
            # Node Ops - Block Prod, Audit, Assurances, etc

            tg.create_task(operate(is_builder))

    except CancelledError:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="cancelled_tasks",
        )

        settings.clear()

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


