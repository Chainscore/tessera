import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from tests.fixtures.dummy_block import create_dummy_block
from .node import Node
from jam.config.logging import logger
from jam.db.kv import KVStore
from .protocols import BlockAnnouncementProtocol


async def block_producer(node: Node, db: KVStore):
    """
    Continuously produces blocks and announces them. 
    Every block is of 6 seconds apart.
    If it is our chance to produce a block, we produce a block and announce it to the network.

    Args:
        node (Node): The network node for communications
        db (KVStore): The database to store the genesis timestamp
    """
    
    # Record genesis timestamp in seconds
    genesis_ts = time()
    up_0 = BlockAnnouncementProtocol()

    block_number = 0
    while True:
        print("time", genesis_ts, time())
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network is not initialized, skipping block production")
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        # Get state from db
        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6

        # Get current timeslot
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.info(f"We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode")

        # Check if we are in fallback or normal tickets
        if state.gamma.s.get_key() == "keys":
            author_key = state.gamma.s.get_value()[ts_epoch_index]
            if author_key == node.validator_data.bandersnatch:
                block = create_dummy_block()
                logger.info(f"⛏️ ({node.name}) Producing Block {block_number}")

                # await announce_block(node, block)
                up_0.transmit(node, block)
            else:
                logger.info(f"🔄 ({node.name}) Skipping Block {block_number}")
        else:
            """Generate a header seal"""
            # TODO: Implement once ring-proof are added
            ...


        # Sleep for remaining time of the timeslot
        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        block_number += 1