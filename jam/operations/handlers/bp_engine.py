from jam.utils.task_utils import create_safe_task

from dot_ring import IETF_VRF, Bandersnatch

from jam.block.extrinsics.tickets import TicketEnvelope
from jam.operations.dispatcher import NodeDispatcher
from jam.finality.finality import Finality

from jam.state.ghost import GhostState
from jam.state.transitions.safrole.safrole import Safrole

from jam.models.protocol.core import TimeSlot, ValidatorIndex
from jam.models.protocol.ticket import TicketBody

from jam.utils.benchmark import write_json
from jam.utils.constants import (
    EPOCH_LENGTH,
    SLOT_PERIOD,
    TICKET_SUBMISSION_END,
    X,
)
from jam.log_setup import block_logger as logger
from jam.utils.util_fns import outside_in


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
        from jam.state.state import state 

        up0 = BlockAnnouncement()

        if not node or len(node.all_connected) == 0:
            logger.debug("Network not initialized - skipping block production")
            return

        latest = Finality.load_latest(settings.main_db)
        if not latest:
            logger.error("Latest not found, node is not configrued", ts=time_slot)
            return

        # If we have already imported a block for this slot
        if state.tau > TimeSlot(time_slot):
            return 

        slot_index = time_slot % EPOCH_LENGTH
        entry = state.gamma.s.unwrap()[slot_index]

        ticket: TicketBody | None = None
        if state.tau // EPOCH_LENGTH != time_slot // EPOCH_LENGTH:
            if time_slot // EPOCH_LENGTH == (state.tau // EPOCH_LENGTH) + 1 and len(state.gamma.a) == EPOCH_LENGTH and slot_index == 0:
                entry = outside_in(state.gamma.a)[slot_index]
            else:
                entry = Safrole.arrange_fallback(state.eta[1], state.gamma.p).unwrap()[slot_index]
        
        if isinstance(entry, TicketBody):
            eta = state.eta[2] if time_slot % EPOCH_LENGTH == 0 else state.eta[3]
            # Use dot_ring for IETF VRF proof and output
            ietf_proof = IETF_VRF[Bandersnatch].prove(
                X.TICKET.value + eta + entry.attempt.encode(),
                settings.bandersnatch_private,
                b"",
            )
            our_id = ietf_proof.proof_to_hash(ietf_proof.output_point)[:32]
            entry_id = entry.id
            if our_id != entry_id:
                logger.debug("⏭ Skipping BP: Not our ticket", sig=entry.id.hex(), our_id=our_id.hex(), entry_id=entry_id.hex())
                return 
            else:
                ticket = entry
        elif entry != settings.bandersnatch_public:
            logger.debug("⏭ Skipping BP: Not our fallback", expected=entry.hex(), our_key=settings.bandersnatch_public.hex())
            return

        # Telemetry: Authoring
        from jam.telemetry import emit_event
        from jam.telemetry.events import Authoring, Authored, BlockOutline
        from tsrkit_types import U32, U64, Bytes32
        
        emit_event(Authoring(slot=U32(time_slot), parent_hash=Bytes32(latest.header.hash().encode())))

        block = latest.produce(TimeSlot(time_slot), state, ticket)

        is_valid = state._force_transition(block)

        if is_valid:
            logger.info(f"⛏ Produced block ({'T' if ticket else 'F'}) {block.header.hash().hex()[:8]+".."}|{time_slot}")
            
            # Telemetry: Authored
            # Construct BlockOutline
            outline = BlockOutline(
                size=U32(len(block.encode())),
                header_hash=Bytes32(block.header.hash().encode()),
                num_tickets=U32(len(block.extrinsic.tickets)),
                num_preimages=U32(len(block.extrinsic.preimages)),
                preimages_size=U32(len(block.extrinsic.preimages)),
                num_guarantees=U32(len(block.extrinsic.guarantees)),
                num_assurances=U32(len(block.extrinsic.assurances)),
                num_disputes=U32(
                    len(block.extrinsic.disputes.verdicts) + 
                    len(block.extrinsic.disputes.culprits) + 
                    len(block.extrinsic.disputes.faults)
                )
            )
            emit_event(Authored(event_id=U64(0), block=outline))
            
            create_safe_task(up0.transmit(BlockAnnouncement.block_to_announcement(block)), name="block_announce")
        else:
            logger.info("😓 Failed to produce a valid block", slot=time_slot, block=block.to_json())