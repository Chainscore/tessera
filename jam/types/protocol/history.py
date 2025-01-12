from dataclasses import dataclass
from typing import List
from jam.types.base.choice import Choice
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import (
    HeaderHash, StateRoot, OpaqueHash
)
from jam.utils.constants import RECENT_HISTORY_SIZE

"""Merkle Mountain Range structure."""
@decodable_vector(element_type=Choice)
class Mmr(Vector[Choice]): ...

@decodable_dataclass
@dataclass
class ReportedWorkPackage(Codable):
    """Reported work package structure."""
    hash: OpaqueHash
    exports_root: OpaqueHash

@decodable_dataclass
@dataclass
class BlockInfo(Codable):
    """Block information structure."""
    header_hash: HeaderHash
    mmr: Mmr
    state_root: StateRoot
    reported: List[ReportedWorkPackage]

"""Fixed-size array of block information."""
@decodable_array(length=RECENT_HISTORY_SIZE, element_type=BlockInfo)
class BlocksHistory(Array[BlockInfo]): ...