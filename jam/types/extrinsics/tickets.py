from dataclasses import dataclass
from jam.types.base.integers.fixed import U8
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import (
    BandersnatchPublic, BandersnatchRingVrfSignature,
    OpaqueHash
)
from jam.utils.constants import EPOCH_LENGTH, MAX_TICKETS_PER_EXTRINSIC
from jam.utils.json.serde import JsonSerde

TicketId = OpaqueHash
TicketAttempt = U8

@decodable_dataclass
@dataclass
class TicketEnvelope(Codable, JsonSerde):
    """Ticket entry structure."""
    attempt: TicketAttempt
    signature: BandersnatchRingVrfSignature

@decodable_dataclass
@dataclass
class TicketBody(Codable, JsonSerde):
    """Ticket body structure."""
    id: TicketId # This is the VRF output of TicketEnvelope.signature https://graypaper.fluffylabs.dev/#/5f542d7/0f84000fbd00
    attempt: TicketAttempt

@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class TicketsAccumulator(Array[TicketBody]): ...

@decodable_array(length=EPOCH_LENGTH, element_type=BandersnatchPublic)
class KeysAccumulator(Array[BandersnatchPublic]): ...

@decodable_vector(element_type=TicketEnvelope, max_length=MAX_TICKETS_PER_EXTRINSIC)
class TicketsExtrinsic(Vector[TicketEnvelope]): ...