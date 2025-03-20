from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.crypto import HeaderHash, StateRoot
from jam.types.protocol.merkle import MMR
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.jstruct import JsonSerde 


@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class PackageDict(Dictionary[WorkPackageHash, SegmentRoot]):
    """Work Package hashes of each item reported (no more than CORE_COUNT)"""

    ...


@decodable_dataclass
@dataclass
class BlockHistory(Codable, JsonSerde):
    """Block history item"""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    packages: PackageDict


@decodable_vector(BlockHistory)
class Beta(Vector[BlockHistory]):
    """Beta state."""

    ...
