from asyncio import CancelledError
from typing import cast

import pytest
import asyncio
import signal
import json
import shutil

from multiprocessing import Process

import logging
import os
import time

from dotenv import load_dotenv
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U16, Uint

from jam.logging import setup_logging
from jam.network.base.certificate import generate_san
from jam.utils.chainspec import chain_config

from jam.consensus.grandpa.finality import Finality
from jam.settings import setup_setting

from jam.network.peer import Peer
from jam.network.node import Node

from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.types.protocol.crypto import BlsPublic
from jam.types.block import Block
from jam.types.protocol.validators import (
    IPAddress,
    ValidatorData,
    ValidatorMetadata,
)

from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.logging import get_logger
from jam.work_package.processor import Processor
from tests.unit.wp.types import RefineVectors, RefineVector

CLIENTS = [
    {"port": 40007, "role": "VALIDATOR", "theme": "matrix", "genesis": True},
]

# Logger for WP Production
logger = get_logger("in_core")


async def start_node(node: Node):
    """Define Node tasks"""

    with open("vectors/combined/combined-001.json", "r") as f:
        data = json.load(f)
        refine_vectors = RefineVectors.from_json(data)

    try:
        processor = Processor(node)
        for i, vector in enumerate(refine_vectors):
            vector = cast(RefineVector, vector)
            wr, wr_hash = processor.process(
                vector.work_package, vector.core_index, vector.extrinsics
            )

            assert wr == vector.work_rep and wr_hash == vector.rep_hash
            print("ASSERTION SUCCESSFUL", i + 1)
    except Exception as e:
        raise e


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

    asyncio.run(
        run_node(genesis_path, env, start_genesis, theme, is_builder, is_validator)
    )


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_refinement():
    print("START OF TEST")

    processes = []

    for client in CLIENTS:
        env_path = f"envs/{client['port']}.env"
        is_validator = client["role"] == "VALIDATOR"
        is_builder = client["role"] == "BUILDER"

        dir_path = f"/data/{client['port']}"

        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"REMOVED DIR: {dir_path}")

        p = Process(
            target=run_node_process,
            args=(
                "",
                env_path,
                client["genesis"],
                client["theme"],
                is_builder,
                is_validator,
            ),
        )
        processes.append(p)

    print("STARTING PROCESSES...")
    for p in processes:
        p.start()

    print("ALL PROCESSES STARTED")

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(5)

    print("TERMINATING PROCESSES")
    for p in processes:
        p.terminate()
    for p in processes:
        p.join()

    print("END OF TEST")


async def run_node(
    genesis_path: str,
    env: str,
    start_genesis: bool,
    theme: str,
    is_builder: bool,
    is_validator: bool,
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

        peers = [
            Peer(id=generate_san(val.ed25519), data=val)
            for val in state.kappa
            if val.metadata.port != port
        ]

        ip = IPAddress.from_str(host)

        tsr_node = Node(
            node_name=name,
            host=str(host),
            port=int(port),
            peers=peers,
            validator_data=ValidatorData(
                settings.bandersnatch_public,
                settings.ed25519_public,
                BlsPublic(bytes(144)),
                ValidatorMetadata(
                    name=Bytes[10](bytes(10)),
                    protocol=Uint[16](2**16 - 1),
                    host=ip,
                    port=U16(port),
                ),
            ),
            is_builder=is_builder,
            is_validator=is_validator,
        )

        block = Block.genesis()
        header_hash = block.save(main_db)
        Finality.set_head(header_hash, main_db)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(tsr_node.initialize())
            tg.create_task(start_node(tsr_node))

    except CancelledError as e:
        logger.info(
            "JAM node shutting down gracefully",
            node_name=name,
            err=e,
            port=port,
            reason="keyboard_interrupt",
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
