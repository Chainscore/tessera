from tsrkit_types import TypedArray, structure, Uint

from .crypto import Hash, OpaqueHash
from jam.utils.constants import EPOCH_LENGTH

TicketId = OpaqueHash
TicketAttempt = Uint[8]


@structure
class TicketBody:
    """Ticket body structure."""

    id: TicketId  # This is the VRF output of TicketEnvelope.signature https://graypaper.fluffylabs.dev/#/5f542d7/0f84000fbd00
    attempt: TicketAttempt

    def __hash__(self) -> int:
        return int.from_bytes(bytes(Hash.blake2b(bytearray(bytes(self.id)) + bytes(self.attempt))))
