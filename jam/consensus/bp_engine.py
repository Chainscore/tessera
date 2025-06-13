import asyncio
import math
from time import time

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
from jam.utils.constants import EPOCH_LENGTH, SLOT_PERIOD
from jam.network.node import Node
from rockstore import RockStore
from jam.utils.dummy.utils import create_dummy_bytes
from jam.config.logging import get_logger

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
        
        logger.info(
            "Block producer initialized",
            node_name=node.name,
            is_validator=node.is_validator,
            validator_key=node.validator_data.bandersnatch.hex()[:16] + "..." if node.validator_data else None
    )

    async def run(self):
        """
        Starts the block producer engine in asyncio loop. 
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """
        from jam.state.state import state

        # Record genesis timestamp in seconds
        genesis_ts = time()
        up0 = BlockAnnouncement()

        logger.info(
            "Starting block producer",
            node_name=self.node.name,
            genesis_timestamp=genesis_ts,
            slot_period=SLOT_PERIOD,
            epoch_length=EPOCH_LENGTH
        )

        # Sleep till we're not synced


        # TODO: If our validator is not in Kappa - skip block production till end of current epoch
        while True:
            if not self.node.is_initialized:
                logger.debug(
                    "Network not initialized - skipping block production",
                    node_name=self.node.name
                )
                await asyncio.sleep(SLOT_PERIOD)
                genesis_ts = time()
                continue

            # Get state from db
            current_timeslot = TimeSlot(math.ceil((time() - genesis_ts) / SLOT_PERIOD))

            # Get current timeslot
            ts_epoch_index = math.floor(int(current_timeslot) % EPOCH_LENGTH)

            # Check if we are in fallback or normal ticket.py
            gamma_s = state.gamma.s.unwrap()

            logger.debug("🔄 Block production cycle", current_timeslot=int(current_timeslot), epoch=ts_epoch_index, gamma_mode=gamma_s.__class__.__name__)

            if isinstance(gamma_s, GammaSFallback):
                author_key = gamma_s[ts_epoch_index]
                
                if author_key == self.node.validator_data.bandersnatch:
                    logger.info(
                        "🧑‍🍳Authoring block - our turn",
                        current_timeslot=int(current_timeslot),
                        epoch=ts_epoch_index,
                        author_key=author_key.hex()[:16] + "..."
                    )
                    
                    block = self._produce_block(state, current_timeslot)
                    block.save(self.db)
                    header_hash = block.header.hash()
                    # Set local chain head to produced block
                    Finality.set_head(header_hash, self.db)
                    # NOTE: We are setting instant finality here, this is to be updated once GRANDPA is implemented
                    Finality.finalise(header_hash, self.db)

                    # Announce
                    up0.transmit(self.node, block)

                    logger.info("🧱Block authored and announced successfully", current_timeslot=int(current_timeslot), block_hash=Hash.blake2b(block.header.encode()).hex()[:16] + "...")
                else:
                    logger.debug(
                        "⏭️ Not our turn to author - skipping", current_timeslot=int(current_timeslot), epoch=ts_epoch_index,
                        expected_author=author_key.hex()[:16] + "...",
                        our_key=self.node.validator_data.bandersnatch.hex()[:16] + "..."
                    )
            else:
                """Generate a header seal"""
                # TODO: Implement once ring-proof are added
                raise NotImplementedError("Only fallback mode is supported for now")

            # Sleep for remaining time of the timeslot
            sleep_duration = 6 - (time() - genesis_ts) % SLOT_PERIOD
            logger.debug("😴 Sleeping until next slot", sleep_duration=sleep_duration)
            await asyncio.sleep(sleep_duration)

    def _produce_block(self, state: State, current_timeslot: TimeSlot) -> Block:
        """
        Produce a block for the given timeslot
        """
        logger.debug(
            "⚒️ Building block components",
            node_name=self.node.name,
            timeslot=int(current_timeslot)
        )
        
        extrinsic = Extrinsic(
            TicketsExtrinsic([]),
            PreimagesExtrinsic([]),
            GuaranteesExtrinsic([]),
            AssurancesExtrinsic([]),
            DisputesExtrinsic(culprits=Culprits([]), faults=Faults([]), verdicts=Verdicts([]))
        )
        
        parent_block = Finality.load_latest(self.db)
        parent_hash = Hash.blake2b(parent_block.header.encode())
        
        block = Block(
            header=Header(
                parent=parent_hash,
                parent_state_root=state.root,
                extrinsic_hash=self.hash_extrinsic(extrinsic),
                slot=current_timeslot,
                epoch_mark=Safrole.get_epoch_marker(state, current_timeslot),
                tickets_mark=Safrole.get_tickets_marker(state, current_timeslot),
                offenders_mark=Disputes.get_offenders_mark(extrinsic.disputes),
                author_index=self.get_author_index(state),
                entropy_source=BandersnatchVrfSignature(create_dummy_bytes(96)),
                seal=BandersnatchVrfSignature(create_dummy_bytes(96))
            ),
            extrinsic=extrinsic
        )
        
        logger.info("Block produced ⛏️", timeslot=int(current_timeslot), block_hash=Hash.blake2b(block.header.encode()).hex()[:16] + "...",)
        
        return block
    
    def get_author_index(self, state: State) -> ValidatorIndex:
        """
        Get block producer's author index from the state
        """
        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == self.node.validator_data.bandersnatch:
                logger.debug(
                    "Found author index in validator set",
                    node_name=self.node.name,
                    author_index=i,
                    validator_key=validator.bandersnatch.hex()[:16] + "..."
                )
                return ValidatorIndex(i)
        
        logger.error(
            "Author not found in validator set",
            node_name=self.node.name,
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
        
        logger.debug(
            "Extrinsic hash computed",
            node_name=self.node.name,
            extrinsic_count=len(all_ext),
            extrinsic_hash=extrinsic_hash.hex()[:16] + "..."
        )
        
        return extrinsic_hash