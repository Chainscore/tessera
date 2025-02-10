"""Refine context types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import (
    HeaderHash, StateRoot, BeefyRoot, OpaqueHash
)
from jam.types.protocol.core import TimeSlot
from jam.utils.json.decorators import json_serializable
from jam.utils.json.serde import JsonSerde

@decodable_vector(OpaqueHash)
class OpaqueHashes(Vector[OpaqueHash]): ...

@json_serializable
@decodable_dataclass
@dataclass
class RefineContext(Codable, JsonSerde):
    """Refine context structure."""
    anchor: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    lookup_anchor: HeaderHash
    lookup_anchor_slot: TimeSlot
    prerequisites: OpaqueHashes
