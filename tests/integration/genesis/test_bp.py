import json
import pytest
import asyncio
import logging
import signal
import os
import time
from multiprocessing import Process

from dotenv import load_dotenv
from jam.logging import setup_logging, logger
from jam.finality.finality import Finality
from jam.settings import setup_setting
from jam.network.node import Node

# from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state
from jam.block import Block
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.operations.handlers.bp_engine import BlockProducer


async def run_node(env: str, theme: str, height: int, db_path: str, is_requester=False):
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = (time.time() - genesis_ts) / SLOT_PERIOD
    init_ep = init_ts // EPOCH_LENGTH

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

    name, port, seed, host = (
        os.environ["NODE_NAME"],
        os.environ["PORT"],
        os.environ["SEED"],
        os.environ["HOST"],
    )

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
    settings = setup_setting(name=name, port=int(port), seed=int(seed), data_path=db_path + "/")

    main_db = settings.main_db

    logger.info(
        "Starting JAM node", name=name, port=port, ts=init_ts, epoch=init_ep, env=environment
    )

    genesis = json.load(open("dev-spec.json"))

    # Set genesis state
    # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
    state = setup_state(settings.state_db, "dev-spec.json")
    # # update_state(state)

    peers = [
        Peer(id=bytes.decode(val.metadata.name, "utf-8"), data=val)
        for val in state.kappa
        if val.metadata.port != port
    ]

    tsr_node = Node(
        node_name=name,
        host=str(host),
        port=int(port),
        peers=peers,
        validator_data=settings.val,
        is_builder=False,
        is_validator=True,
    )

    block = Block.decode(bytes.fromhex(genesis["genesis_header"]))
    header_hash = block.save(main_db)
    Finality.set_head(header_hash, main_db)
    Finality.finalise(header_hash, main_db)

    # Generate random blocks upto height
    for i in range(1, height + 1):
        i_block = BlockProducer(tsr_node, main_db)._produce_block(state, TimeSlot(i))
        state.transition(i_block)
        i_block.save(main_db)

        hh = HeaderHash(i_block.header.hash())

        Finality.set_head(hh, main_db)
        Finality.finalise(hh, main_db)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(tsr_node.initialize())
        tg.create_task(BlockProducer(tsr_node, main_db).run())


session_name = "jam_test"


def run_node_process(env: str, theme: str, db_path: str, height=0, req=False):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_node(env, theme, height, req, db_path))


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_128(db_path):
    node_processes = []
    node_processes.append(
        Process(target=run_node_process, args=("envs/40000.env", "matrix", 10, False, db_path))
    )
    node_processes.append(
        Process(target=run_node_process, args=("envs/40001.env", "polkadot", 10, False, db_path))
    )
    node_processes.append(
        Process(target=run_node_process, args=("envs/40002.env", "bitcoin", 10, False, db_path))
    )
    node_processes.append(
        Process(target=run_node_process, args=("envs/40003.env", "default", 10, False, db_path))
    )

    for pr in node_processes:
        pr.start()

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(10)

    for pr in node_processes:
        pr.terminate()
        pr.join()
