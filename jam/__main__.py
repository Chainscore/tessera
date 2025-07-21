import asyncio
import json
import logging
import os
import time

from asyncio import CancelledError
from dotenv import load_dotenv
from jam.operations.operator import operate
from jam.api.rpc.app import rpc
from jam.logging import setup_logging, logger
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config
from jam.settings import setup_setting
from jam.consensus.grandpa.finality import Finality
from jam.network.peer import Peer
from jam.network.node import setup_node
from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.types.block import Block
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD, EPOCH_LENGTH

from jam.network.protocols.ce_144 import AuditAnnouncement
from jam.network.protocols.ce_145 import JudgmentPublication
from tests.unit.test_judgment import data144, data145
from jam.audit.audit_process import AuditProcess
from jam.audit.q import sample_work_reports_with_nulls

CE144 = AuditAnnouncement()
CE145 = JudgmentPublication()


async def main(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
) -> None:
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS         # Actual Genesis time for JAM Common Era
    init_ts = int((time.time() - genesis_ts) // SLOT_PERIOD)
    init_ep = int(init_ts // EPOCH_LENGTH)


    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env,override=True)

    name = os.environ["NODE_NAME"]
    port = os.environ["PORT"]
    seed = os.environ["SEED"]
    host = os.environ["HOST"]
    logger.info("SET HOST", host=host, port=port)

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
    settings = setup_setting(name=name, port=int(port), seed=int(seed), data_path=f"data/")

    main_db = settings.main_db

    logger.info(
        "Starting JAM node", name=name, port=port,
        ts=init_ts, epoch=init_ep, spec=chain_config.name,
    )

    try:
        # -------------- SETUP STATE -------------
        # Set genesis state
        dev_spec = json.load(open(genesis_path))
        # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
        state = setup_state(settings.state_db, genesis_path)
        state.store.disable_cache()
        update_state(state)

        # ----------- SETUP NETWORKING ------------
        peers = [
            Peer(data=val)
            for val in state.kappa
            if val.metadata.port != port
        ]

        tsr_node = setup_node(
            name, int(port), peers, host=str(host),
            is_bd=is_builder, is_val=is_validator
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
            if int(tsr_node.port) == 40000:
                await asyncio.sleep(5)
                # tg.create_task(CE144.transmit(node=tsr_node, data=data144))
                # tg.create_task(CE145.transmit(node=tsr_node, data=data145))
                newly_list = sample_work_reports_with_nulls( "jam/combine.json",total_items=10, null_count=0)
                #
                # tg.create_task(AuditProcess.audit_process(newly_avail_wrs=newly_list))


    except CancelledError:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="cancelled_tasks"
        )

        # FOR SAVING TEST VECTORS
        # print("CANCELLED")
        # from jam.utils.benchmark import write_json
        # from jam.operations.builder import vectors
        # write_json("vectors/combined", vectors.to_json())

        settings.clear()

    except KeyboardInterrupt:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            port=port,
            reason="keyboard_interrupt"
        )

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
