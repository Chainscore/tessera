from dataclasses import dataclass
from typing import List
from jam.types.protocol.merkle import MMR
from jam.types.base.sequences.array import Array, decodable_array
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import HeaderHash, StateRoot, OpaqueHash
from jam.utils.constants import RECENT_HISTORY_SIZE
from jam.utils.json.serde import JsonSerde


@decodable_dataclass
@dataclass
class ReportedWorkPackage(Codable, JsonSerde):
    """Reported work package structure."""

    hash: OpaqueHash
    exports_root: OpaqueHash


@decodable_dataclass
@dataclass
class BlockInfo(Codable, JsonSerde):
    """Block information structure."""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    reported: List[ReportedWorkPackage]


"""Fixed-size array of block information."""


@decodable_array(length=RECENT_HISTORY_SIZE, element_type=BlockInfo)
class BlocksHistory(Array[BlockInfo]):
    ...
