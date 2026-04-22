from jam.block.extrinsics.store import ExtrinsicStore
from tsrkit_types.sequences import TypedBoundedVector
from tsrkit_types.struct import structure
from jam.models.protocol.crypto import BandersnatchRingVrfSignature
from jam.models.protocol.ticket import TicketAttempt
from jam.utils.constants import MAX_TICKETS_PER_EXTRINSIC


@structure
class TicketEnvelope:
    """Ticket entry structure."""

    attempt: TicketAttempt
    signature: BandersnatchRingVrfSignature


TicketsExtrinsic = TypedBoundedVector[TicketEnvelope, 0, MAX_TICKETS_PER_EXTRINSIC]

ticket_store = ExtrinsicStore[TicketEnvelope]()
