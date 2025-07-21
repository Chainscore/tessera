from jam.operations.dispatcher import NodeDispatcher
from jam.consensus.grandpa.finality import Finality
from jam.consensus.safrole.safrole import Safrole
from jam.disputes.disputes import Disputes
from jam.network.protocols.up_0 import BlockAnnouncement
from jam.state.state import State
from jam.types import AssurancesExtrinsic
from jam.types.block import (
    Block,
    Header,
    TicketsExtrinsic,
    GuaranteesExtrinsic,
)
from jam.types.block.extrinsics.extrinsic import Extrinsic
from jam.types.block.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature, Hash, OpaqueHash
from jam.types.state.gamma import GammaSFallback
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH, MAX_TICKETS_PER_EXTRINSIC, SLOT_PERIOD, GENESIS_TS
from jam.utils.dummy.utils import create_dummy_bytes
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
        from jam.network.node import node
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
                logger.debug("🧑‍🍳Authoring block - our turn", ts=time_slot, epoch=(time_slot//SLOT_PERIOD))
                block = cls._produce_block(state, TimeSlot(time_slot))
                state._force_transition(block)
                # Announce
                await up0.transmit(node, block)
                logger.error("⛏️ Block produced & announced", curr_timeslot=int(time_slot), block_hash=Hash.blake2b(block.header.encode()).hex()[:16] + "...", wr_len=len(block.extrinsic.guarantees), as_len=len(block.extrinsic.assurances))
            else:
                logger.debug("⏭️ Not our turn to author - skipping", curr_timeslot=int(time_slot), epoch=(time_slot//SLOT_PERIOD), expected_author=author_key.hex()[:16] + "...")
        else:
            """Generate a header seal"""
            # TODO: Implement once ring-proof are added
            raise NotImplementedError("Only fallback mode is supported for now")

    @classmethod
    def _produce_block(cls, state: State, curr_ts: TimeSlot) -> Block:
        """
        Produce a block for the given timeslot
        """
        eg, et, ea, ep = GuaranteesExtrinsic([]), [], [], []
        from .ext_store import ext_store
        from jam.settings import settings
        for rg in ext_store.eg:
            # TODO: Filtering - Take only one WR per core [?]
            eg.append(rg)
            if len(eg) >= CORE_COUNT:
                break
        ep = ext_store.ep
        et = TicketsExtrinsic(ext_store.et[:MAX_TICKETS_PER_EXTRINSIC])
        ea = AssurancesExtrinsic(sorted(ext_store.ea, key=lambda a:a.validator_index))
        extrinsic = Extrinsic(et, ep, eg, ea, ext_store.ed)

        parent_block = Finality.load_latest(settings.main_db)
        parent_hash = Hash.blake2b(parent_block.header.encode())

        block = Block(
            header=Header(
                parent=parent_hash,
                parent_state_root=state.root,
                extrinsic_hash=cls.hash_extrinsic(extrinsic),
                slot=curr_ts,
                epoch_mark=Safrole.get_epoch_marker(state, curr_ts),
                tickets_mark=Safrole.get_tickets_marker(state, curr_ts),
                offenders_mark=Disputes.get_offenders_mark(extrinsic.disputes),
                author_index=cls.get_author_index(state),
                entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96)),
                seal=BandersnatchVrfSignature(create_dummy_bytes(96))
            ),
            extrinsic=extrinsic
        )

        return block

    @staticmethod
    def get_author_index(state: State) -> ValidatorIndex:
        """
        Get block producer's author index from the state
        """
        from jam.network.node import node
        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == node.validator_data.bandersnatch:
               return ValidatorIndex(i)

        logger.error("Author not found in validator set", our_key=node.validator_data.bandersnatch)
        raise ValueError("Author not found in the state")

    @staticmethod
    def hash_extrinsic(extrinsic: Extrinsic) -> OpaqueHash:
        all_ext = [
            extrinsic.tickets,
            extrinsic.preimages,
            extrinsic.guarantees,
            extrinsic.assurances,
            extrinsic.disputes
        ]
        enc_ext = b''
        for ext in all_ext:
            enc_ext += bytes(Hash.blake2b(ext.encode()))

        extrinsic_hash = Hash.blake2b(enc_ext)

        return extrinsic_hash
