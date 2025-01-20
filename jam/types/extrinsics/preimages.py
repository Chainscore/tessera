"""Preimage-related extrinsic types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.types.protocol.core import ServiceId

@decodable_dataclass
@dataclass
class Preimage(Codable):
    """Preimage structure."""
    requester: ServiceId
    blob: Bytes

@decodable_vector(Preimage)
class PreimagesExtrinsic(Vector[Preimage]): ...
