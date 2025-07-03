import asyncio
from time import time

from jam.storage.stores import (guarantee_store, dispute_store, preimage_store, ticket_store, assurance_store)
from jam.consensus.grandpa.finality import Finality
from jam.consensus.safrole.safrole import Safrole
from jam.disputes.disputes import Disputes
from jam.network.protocols.up_0 import BlockAnnouncement
from jam.state.state import State
from jam.types.block import (
    Block, 
    Header,
    TicketsExtrinsic,
    PreimagesExtrinsic,
    GuaranteesExtrinsic,
    AssurancesExtrinsic,
    DisputesExtrinsic,
)
from jam.types.block.extrinsics.extrinsic import Extrinsic
from jam.types.block.extrinsics.disputes import Culprits, Faults, Verdicts
from jam.types.protocol.core import TimeSlot, ValidatorIndex
from jam.types.protocol.crypto import BandersnatchVrfSignature, Hash, OpaqueHash
from jam.types.state.gamma import GammaSFallback
from jam.utils.constants import CORE_COUNT, EPOCH_LENGTH, SLOT_PERIOD, GENESIS_TS
from jam.network.node import Node
from rockstore import RockStore
from jam.utils.dummy.utils import create_dummy_bytes
from jam.logging import get_logger

# Logger for Block Production / Authoring module
logger = get_logger("author")

class BlockProducer:
    """
    BP Engine: Continuously produces blocks and announces them. Every block is of SLOT_PERIOD seconds apart.
    If it is our chance to produce a block, we produce a block and announce it to the network.

    Args:
        node (Node): The network node for communications
        db (RockStore): The database to store the genesis timestamp
    """

    node: Node
    db: RockStore

    def __init__(self, node: Node, db: RockStore):
        self.node = node
        self.db = db

        logger.info("Block producer initialized", validator_key=node.validator_data.bandersnatch.hex()[:16] + "..." if node.validator_data else None)

    async def run(self):
        """
        Starts the block producer engine in asyncio loop. 
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """

        up0 = BlockAnnouncement()

        logger.info(
            "Starting block producer",
            genesis_timestamp=GENESIS_TS,
            slot_period=SLOT_PERIOD,
            epoch_length=EPOCH_LENGTH
        )

        # Sleep till we're not synced

        # TODO: If our validator is not in Kappa - skip block production till end of current epoch
        while True:
            from jam.state.state import state
            if not self.node.is_initialized:
                logger.debug(
                    "Network not initialized - skipping block production",
                    node_name=self.node.name
                )
                await asyncio.sleep(SLOT_PERIOD)
                continue

            # Get current timeslot
            curr_ts = TimeSlot((time() - GENESIS_TS) // SLOT_PERIOD)
            curr_ep = int(curr_ts % EPOCH_LENGTH)

            # Check if we are in fallback or normal ticket.py
            gamma_s = state.gamma.s.unwrap()

            logger.debug("🔄 Block production cycle", curr_timeslot=int(curr_ts), epoch=curr_ep, gamma_mode=gamma_s.__class__.__name__)

            if isinstance(gamma_s, GammaSFallback):
                author_key = gamma_s[curr_ep]

                if author_key == self.node.validator_data.bandersnatch:
                    logger.debug(
                        "🧑‍🍳Authoring block - our turn",
                        ts=int(curr_ts), epoch=curr_ep, author=author_key.hex()[:16] + "..."
                    )

                    block = self._produce_block(state, curr_ts)
                    state.transition(block)
                    # Announce
                    await up0.transmit(self.node, block)

                    logger.debug("🧱Block produced & announced", curr_timeslot=int(curr_ts), block_hash=Hash.blake2b(block.header.encode()).hex()[:16] + "...")
                else:
                    logger.debug(
                        "⏭️ Not our turn to author - skipping", curr_timeslot=int(curr_ts), epoch=curr_ep,
                        expected_author=author_key.hex()[:16] + "...",
                        our_key=self.node.validator_data.bandersnatch.hex()[:16] + "..."
                    )
            else:
                """Generate a header seal"""
                # TODO: Implement once ring-proof are added
                raise NotImplementedError("Only fallback mode is supported for now")

            # Sleep for remaining time of the timeslot
            sleep_duration = SLOT_PERIOD - (time() - GENESIS_TS) % SLOT_PERIOD
            logger.debug("😴 Sleeping until next slot", sleep_duration=sleep_duration)
            await asyncio.sleep(sleep_duration)
    

    def _produce_block(self, state: State, curr_ts: TimeSlot) -> Block:
        """
        Produce a block for the given timeslot
        """
        logger.debug("⚒️ Building block components", timeslot=int(curr_ts))
        
        eg, et, ea, ep = [], [], [], []
        from .ext_store import ext_store
        for rg in ext_store.eg:
            # TODO: Take only one WR per core [?]
            eg.append(rg)
            if len(eg) >= CORE_COUNT:
                break 

        extrinsic = Extrinsic(
            TicketsExtrinsic(et),
            PreimagesExtrinsic(ep),
            GuaranteesExtrinsic(eg),
            AssurancesExtrinsic(ea),
            DisputesExtrinsic(culprits=Culprits([]), faults=Faults([]), verdicts=Verdicts([]))
        )

        parent_block = Finality.load_latest(self.db)
        parent_hash = Hash.blake2b(parent_block.header.encode())

        block = Block(
            header=Header(
                parent=parent_hash,
                parent_state_root=state.root,
                extrinsic_hash=self.hash_extrinsic(extrinsic),
                slot=curr_ts,
                epoch_mark=Safrole.get_epoch_marker(state, curr_ts),
                tickets_mark=Safrole.get_tickets_marker(state, curr_ts),
                offenders_mark=Disputes.get_offenders_mark(extrinsic.disputes),
                author_index=self.get_author_index(state),
                entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96)),
                seal=BandersnatchVrfSignature(create_dummy_bytes(96))
            ),
            extrinsic=extrinsic
        )

        logger.info("Block produced ⛏️", timeslot=int(curr_ts), block_hash=Hash.blake2b(block.header.encode()).hex()[:16] + "...",)

        return block

    def get_author_index(self, state: State) -> ValidatorIndex:
        """
        Get block producer's author index from the state
        """
        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == self.node.validator_data.bandersnatch:
               return ValidatorIndex(i)

        logger.error(
            "Author not found in validator set",
            our_key=self.node.validator_data.bandersnatch.hex()[:16] + "...",
            validator_count=len(state.kappa)
        )
        raise ValueError("Author not found in the state")
    
    def hash_extrinsic(self, extrinsic: Extrinsic) -> OpaqueHash:
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
