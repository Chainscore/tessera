from jam.operations.dispatcher import NodeDispatcher
from jam.finality.finality import Finality
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.state.gamma import GammaSFallback
from jam.utils.constants import (
    EPOCH_LENGTH,
    SLOT_PERIOD,
)
from jam.logging import get_logger

# Logger for Block Production / Authoring module
logger = get_logger("author")


class BlockProducer(NodeDispatcher):
    """
    BP Engine: Continuously produces blocks and announces them. Every block is of SLOT_PERIOD seconds apart.
    If it is our chance to produce a block, we produce a block and announce it to the network.
    """

    @classmethod
    async def run(cls, time_slot: int):
        """
        Starts the block producer engine in asyncio loop.
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """
        from jam.network.start import node
        from jam.settings import settings
        from jam.network.protocols.up_0 import BlockAnnouncement

        up0 = BlockAnnouncement()

        # TODO: If our validator is not in Kappa - skip block production till end of current epoch
        from jam.state.state import state

        if not node.is_initialized:
            logger.debug("Network not initialized - skipping block production")
            return

        # Check if we are in fallback or normal tickets
        gamma_s = state.gamma.s.unwrap()

        if isinstance(gamma_s, GammaSFallback):
            author_key = gamma_s[time_slot % EPOCH_LENGTH]

            if author_key == node.validator_data.bandersnatch:
                logger.debug(
                    "🧑‍🍳Authoring block - our turn",
                    ts=time_slot,
                    epoch=(time_slot // SLOT_PERIOD),
                )

                curr_block = Finality.load_latest(settings.main_db)
                if curr_block is None:
                    raise ValueError(
                        f"Latest Block not found. Node was not initiated properly. Timeslot = {time_slot}"
                    )

                new_block = curr_block.produce(TimeSlot(time_slot))

                state.transition(new_block)
                # Announce
                await up0.transmit(node, new_block)
                logger.info(
                    "⛏️ Block produced & announced",
                    curr_timeslot=int(time_slot),
                    block_hash=Hash.blake2b(new_block.header.encode()).hex()[:16] + "...",
                )
            else:
                logger.debug(
                    "⏭️ Not our turn to author - skipping",
                    curr_timeslot=int(time_slot),
                    epoch=(time_slot // SLOT_PERIOD),
                    expected_author=author_key.hex()[:16] + "...",
                )
        else:
            """Generate a header seal"""
            # TODO: Implement once ring-proof are added
            raise NotImplementedError("Only fallback mode is supported for now")
