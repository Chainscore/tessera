import asyncio

from py_ark_vrf import prove_ietf, vrf_output
from jam.block.extrinsics.tickets import TicketEnvelope
from jam.operations.dispatcher import NodeDispatcher
from jam.finality.finality import Finality
from jam.state.transitions.safrole.safrole import Safrole
from jam.types.protocol.core import TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.protocol.ticket import TicketBody
from jam.types.state.gamma import GammaS, GammaSFallback, GammaSTickets
from jam.utils.constants import (
    EPOCH_LENGTH,
    SLOT_PERIOD,
    TICKET_SUBMISSION_END,
    X,
)
from jam.logging import get_logger
from jam.utils.util_fns import outside_in

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

        ticket = None
        if state.tau // EPOCH_LENGTH != time_slot // EPOCH_LENGTH:
            if time_slot // EPOCH_LENGTH == (state.tau // EPOCH_LENGTH) + 1 and len(state.gamma.a) == EPOCH_LENGTH and slot_index >= TICKET_SUBMISSION_END:
                entry = outside_in(state.gamma.a)[slot_index]
            else:
                entry = Safrole.arrange_fallback(state.eta[1], state.gamma.k).unwrap()[slot_index]
        
        if isinstance(entry, TicketBody):
            eta = state.eta[2] if time_slot % EPOCH_LENGTH == 0 else state.eta[3]
            our_id = vrf_output(
                prove_ietf(
                    settings.bandersnatch_private,
                    X.TICKET.value + eta.encode() + entry.attempt.encode(), b""
                )
            )
            entry_id = entry.id
            if our_id != entry_id:
                logger.debug("⏭ Skipping BP: Not our ticket", sig=entry.id.hex(), our_id=our_id.hex(), entry_id=entry_id.hex())
                return 
            else:
                ticket = entry
        elif entry != settings.bandersnatch_public:
            logger.debug("⏭ Skipping BP: Not our fallback", expected=entry, our_key=settings.bandersnatch_public.hex())
            return

        block = latest.produce(TimeSlot(time_slot), ticket)

        if state.transition(block):
            if ticket:
                logger.info("⛏ Produced block using ticket", hash=block.header.hash().hex()[:16] + "...", slot=time_slot)
            else:
                logger.info("⛏ Produced block", hash=block.header.hash().hex()[:16]+"...", slot=time_slot)
            asyncio.create_task(up0.transmit(BlockAnnouncement.block_to_announcement(block)))
        else:
            logger.info("😓 Failed to produce a valid block", slot=time_slot, block=block)

