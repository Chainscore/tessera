from dataclasses import dataclass
from jam.types.base.integers.fixed import U8
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import (
    BandersnatchPublic, BandersnatchRingVrfSignature,
    OpaqueHash
)
from jam.utils.constants import EPOCH_LENGTH

TicketId = OpaqueHash
TicketAttempt = U8

@decodable_dataclass
@dataclass
class TicketEnvelope(Codable):
    """Ticket entry structure."""
    attempt: TicketAttempt
    signature: BandersnatchRingVrfSignature

@decodable_dataclass
@dataclass
class TicketBody(Codable):
    """Ticket body structure."""
    id: TicketId
    attempt: TicketAttempt

@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class TicketsAccumulator(Array[TicketBody]): ...

@decodable_array(length=EPOCH_LENGTH, element_type=BandersnatchPublic)
class KeysAccumulator(Array[BandersnatchPublic]): ...

@decodable_vector(TicketEnvelope)
class TicketsExtrinsic(Vector[TicketEnvelope]): ...