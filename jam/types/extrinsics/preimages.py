"""Preimage-related extrinsic types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.core import ServiceId
from jam.utils.json.decorators import json_serializable
from jam.utils.json.serde import JsonSerde

@json_serializable
@decodable_dataclass
@dataclass
class Preimage(Codable, JsonSerde):
    """Preimage structure."""
    requester: ServiceId
    blob: Bytes

@decodable_vector(Preimage)
class PreimagesExtrinsic(Vector[Preimage]): ...
