import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from .node import Node
from jam.config.logging import logger
from jam.db.kv import KVStore
from tests.fixtures.dummy_package import create_dummy_package


async def wp_producer(node: Node, db: KVStore):
    """
    Continuously produces work packages and transmits them.
    A builder node produces a work package and share it with the guarantors.
    Args:
        node (Node): The network node for communications
        db (KVStore): The database to store the genesis timestamp
    """

    # Record genesis timestamp in seconds
    genesis_ts = time()

    wp_iter = 0
    while True:
        print("time", genesis_ts, time())
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network is not initialized, skipping packages production")
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        # Get state from db
        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6

        # Get current timeslot
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.info(f"We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode")

        if node.is_builder:
            wp = create_dummy_package()
            logger.info(f"⛏️ ({node.name}) Producing Work Package {wp.authorizer}")
            # TODO: Implement package transmission


        # Sleep for remaining time of the timeslot
        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        wp_iter += 1