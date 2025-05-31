from dataclasses import dataclass

from jam.types.base import decodable_dictionary, Dictionary
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import WorkPackageHash, SegmentRoot
from jam.types.protocol.crypto import HeaderHash, StateRoot
from jam.merklization.mountain_merkle import MMR
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde

@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot,key_name="hash", value_name="exports_root")
class WPHashes(Dictionary[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

@decodable_dataclass
@dataclass
class BlockHistory(Codable, JsonSerde):
    """Block history item"""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    reported: WPHashes


@decodable_vector(BlockHistory)
class Beta(Vector[BlockHistory]):
    """Beta state."""
    ...
