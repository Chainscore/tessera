from dataclasses import dataclass
from jam.types import Vector
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.crypto import MMR, HeaderHash, StateRoot
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class PackageDict(Dictionary[WorkPackageHash, SegmentRoot]): 
    """Work Package hashes of each item reported (no more than CORE_COUNT)"""
    ...

@decodable_dataclass
@dataclass
class BlockHistory(Codable):
    """Block history item"""
    header_hash: HeaderHash
    mmr_root: MMR
    state_root: StateRoot
    packages: PackageDict

@decodable_vector(BlockHistory)
class Beta(Vector[BlockHistory]): 
    """Beta state."""
    ...