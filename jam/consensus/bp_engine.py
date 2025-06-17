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
from jam.utils.constants import EPOCH_LENGTH, SLOT_PERIOD
from jam.network.node import Node
from jam.config.logging import logger
from rockstore import RockStore
from jam.utils.dummy.utils import create_dummy_bytes

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

    async def run(self):
        """
        Starts the block producer engine in asyncio loop. 
        Assumes that the node is initialized and the latest synchronized state is stored in the db.
        """

        # Record genesis timestamp in seconds
        genesis_ts = time()
        up0 = BlockAnnouncement()

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
            current_timeslot = TimeSlot(math.ceil((time() - genesis_ts) / SLOT_PERIOD))

            # Get current timeslot
            ts_epoch_index = math.floor(int(current_timeslot) % EPOCH_LENGTH)

            logger.info(
                f"🔄 ({self.node.name}) We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode"
            )

            # Check if we are in fallback or normal ticket.py
            if state.gamma.s.get_key() == "keys":
                author_key = state.gamma.s.get_value()[ts_epoch_index]
                if author_key == self.node.validator_data.bandersnatch:
                    block = self._produce_block(state, current_timeslot)
                    # Set local chain head to produced block
                    Finality.set_head(current_timeslot, self.db)
                    # NOTE: We are setting instant finality here, this is to be updated once GRANDPA is implemented
                    Finality.finalise(current_timeslot, self.db)
                    # Announce
                    up0.transmit(self.node, block)
                else:
                    logger.info(f"🔄 ({self.node.name}) Skipping Block for TS {current_timeslot}")
            else:
                """Generate a header seal"""
                # TODO: Implement once ring-proof are added
                raise NotImplementedError("Only fallback mode is supported for now")
                ...

            # Sleep for remaining time of the timeslot
            await asyncio.sleep(6 - (time() - genesis_ts) % SLOT_PERIOD)

    def _produce_block(self, state: State, current_timeslot: TimeSlot) -> Block:
        """
        Produce a block for the given timeslot
        """
        extrinsic = Extrinsic(
            TicketsExtrinsic([]),
            PreimagesExtrinsic([]),
            GuaranteesExtrinsic([]),
            AssurancesExtrinsic([]),
            DisputesExtrinsic(culprits=Culprits([]), faults=Faults([]), verdicts=Verdicts([]))
        )
        return Block(
            header=Header(
                parent=Hash.blake2b(Block.load_parent(current_timeslot, self.db).header.encode()),
                parent_state_root=state.generate_root(),
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
    
    def get_author_index(self, state: State) -> ValidatorIndex:
        """
        Get block producer's author index from the state
        """
        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == self.node.validator_data.bandersnatch:
                return ValidatorIndex(i)
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
        return Hash.blake2b(enc_ext)