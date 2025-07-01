import pytest
import asyncio
import logging
import signal
import os
import time
from multiprocessing import Process

from tsrkit_types import U32
from dotenv import load_dotenv
from jam.logging import setup_logging, logger
from jam.consensus.grandpa.finality import Finality
from jam.network.protocols.ce_128 import BlockRequest, CE128Data, Direction
from jam.network.protocols.up_0 import Final
from jam.settings import setup_setting
from jam.network.peer import Peer
from jam.network.node import Node
from jam.operations.utils.state_update import update_state
from jam.state.state import setup_state, State
from jam.types.block import Block
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import HeaderHash
from jam.utils.constants import GENESIS_TS, EPOCH_LENGTH, SLOT_PERIOD
from jam.consensus.bp_engine import BlockProducer

clients = [40000, 40001]

TENTH_HH = "a18affdfdcf9ab1959e58a826d8b34aa65a9106b2efef0eaa59dda2085ee6599"

async def _test_blocks_requests(node: Node, main_db):
    await asyncio.sleep(5)

    for peer in node.peer_conn:
        num_blocks = 5 

        protocol = BlockRequest()
        message = CE128Data(
            header=HeaderHash(main_db.get(Finality.FINAL_KEY)), 
            dir=Direction.AscExc, 
            max_blocks=U32(num_blocks)
        )

        responses = await protocol.transmit(node, message)
        print(f"ASC {message.header.hex()} [max={num_blocks}] {[bl.header.hash().hex() for bl in responses[0]]}")
        assert len(responses[0]) == min(num_blocks, 10)
        
    for peer in node.peer_conn:
        num_blocks = 5 
        
        protocol = BlockRequest()
        message = CE128Data(
            header=HeaderHash.fromhex(TENTH_HH), 
            dir=Direction.DesInc, 
            max_blocks=U32(num_blocks)
        )
        responses = await protocol.transmit(node, message)
        print(f"DSC {TENTH_HH} [max={num_blocks}] {[bl.header.hash().hex() for bl in responses[0]]}")
        assert len(responses[0]) == min(num_blocks, 10)



async def run_node(env: str, theme: str, height: int, is_requester = False):
    # ---------- SETUP LOGGING ----------
    genesis_ts = GENESIS_TS  # Actual Genesis time for JAM Common Era
    init_ts = (time.time() - genesis_ts) / SLOT_PERIOD
    init_ep = init_ts // EPOCH_LENGTH

    # ---------- LOAD ENVIRONMENT ----------
    load_dotenv(".env")
    load_dotenv(env, override=True)

    name, port, seed, host = os.environ["NODE_NAME"], os.environ["PORT"], os.environ["SEED"], os.environ["HOST"]

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

    logger.info("Starting JAM node", name=name, port=port, ts=init_ts, epoch=init_ep, env=environment)

    # Set genesis state
    # Regardless whether we are starting from genesis or not - b/c we'll be doing full sync
    state = setup_state(settings.state_db, "dev-spec.json")
    update_state(state)

    peers = [
        Peer(
            id=bytes.decode(val.metadata.name, 'utf-8'),
            data=val
        )
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

    block = Block.genesis()
    header_hash = block.save(main_db)
    Finality.set_head(header_hash, main_db)
    Finality.finalise(header_hash, main_db)

    # Generate random blocks upto height 
    for i in range(1, height+1):
        i_block = BlockProducer(tsr_node, main_db)._produce_block(state, TimeSlot(i))
        i_block.save(main_db)

        hh = HeaderHash(i_block.header.hash())

        Finality.set_head(hh, main_db)
        Finality.finalise(hh, main_db)

    async with asyncio.TaskGroup() as tg:
        tg.create_task(tsr_node.initialize())
        if is_requester: tg.create_task(_test_blocks_requests(tsr_node, settings.main_db))

session_name = "jam_test"

def run_node_process(env: str, theme: str, height = 0, req = False):
    # Handle clean termination
    def handle_sigterm(signum, frame):
        exit(0)
    signal.signal(signal.SIGTERM, handle_sigterm)

    asyncio.run(run_node(env, theme, height, req))

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_128():
    p_alice = Process(
        target=run_node_process,
        args=('envs/40000.env', "matrix", 10, False)
    )
    p_bob = Process(
        target=run_node_process,
        args=('envs/40001.env', "polkadot", 0, True)
    )

    p_alice.start()
    p_bob.start()

    # KEEP TEST ALIVE FOR SOME TIME
    await asyncio.sleep(10)

    print("END OF TEST")

    p_alice.terminate()
    p_bob.terminate()
    p_alice.join()
    p_bob.join()

