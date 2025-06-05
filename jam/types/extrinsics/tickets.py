from tsrkit_types.integers import Uint
from tsrkit_types.sequences import TypedArray, TypedVector, TypedBoundedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingVrfSignature,
    OpaqueHash,
)
from jam.utils.constants import EPOCH_LENGTH, MAX_TICKETS_PER_EXTRINSIC
from jam.types.protocol.crypto import Hash

TicketId = OpaqueHash
TicketAttempt = Uint[8]

@structure
class TicketEnvelope:
    """Ticket entry structure."""

    attempt: TicketAttempt
    signature: BandersnatchRingVrfSignature


@structure
class TicketBody:
    """Ticket body structure."""

    id: TicketId  # This is the VRF output of TicketEnvelope.signature https://graypaper.fluffylabs.dev/#/5f542d7/0f84000fbd00
    attempt: TicketAttempt

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.blake2b(bytearray(bytes(self.id)) + bytes(self.attempt))))


TicketsAccumulator = TypedArray[TicketBody, EPOCH_LENGTH]

KeysAccumulator = TypedArray[BandersnatchPublic, EPOCH_LENGTH]

TicketsExtrinsic = TypedBoundedVector[TicketEnvelope, 0, MAX_TICKETS_PER_EXTRINSIC]