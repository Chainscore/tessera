import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.types.block import Block
from jam.utils.constants import EPOCH_LENGTH, SLOT_PERIOD
from jam.network.node import Node
from jam.config.logging import logger
from jam.db.kv import KVStore
from tests.fixtures.dummy_block import create_dummy_block

class BlockProducer:
    """
    BP Engine: Continuously produces blocks and announces them. Every block is of SLOT_PERIOD seconds apart.
    If it is our chance to produce a block, we produce a block and announce it to the network.

    Args:
        node (Node): The network node for communications
        db (KVStore): The database to store the genesis timestamp
    """

    node: Node
    db: KVStore

    def __init__(self, node: Node, db: KVStore):
        self.node = node
        self.db = db

    async def run(self):
        """
        Starts the block producer engine in asyncio loop. 
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """

        # Record genesis timestamp in seconds
        genesis_ts = time()

        # TODO: If our validator is not in Kappa - skip block production till end of current epoch
        while True:
            if not self.node.is_initialized:
                logger.info(
                    f"🔄 ({self.node.name}) Network is not initialized, skipping block production"
                )
                await asyncio.sleep(SLOT_PERIOD)
                genesis_ts = time()
                continue

            # Get state from db
            state = State.load(self.db)
            current_timeslot = (time() - genesis_ts) // SLOT_PERIOD

            # Get current timeslot
            ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

            logger.info(
                f"🔄 ({self.node.name}) We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode"
            )

            # Check if we are in fallback or normal tickets
            if state.gamma.s.get_key() == "keys":
                author_key = state.gamma.s.get_value()[ts_epoch_index]
                if author_key == self.node.validator_data.bandersnatch:
                    block = await self._produce_block(state, current_timeslot)
                    logger.info(f"⛏️ ({self.node.name}) Producing Block for TS {current_timeslot}")
                    for client in self.node.connections:
                        await client.send_message(block.encode())
                else:
                    logger.info(f"🔄 ({self.node.name}) Skipping Block for TS {current_timeslot}")
            else:
                """Generate a header seal"""
                # TODO: Implement once ring-proof are added
                ...

            # Sleep for remaining time of the timeslot
            await asyncio.sleep(6 - (time() - genesis_ts) % SLOT_PERIOD)

    async def _produce_block(self, state: State, current_timeslot: int) -> Block:
        """
        Produce a block for the given timeslot
        """
        return create_dummy_block()
