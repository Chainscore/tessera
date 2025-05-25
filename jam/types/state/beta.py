from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.protocol.crypto import HeaderHash, StateRoot
from jam.merklization.mountain_merkle import MMR
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde, with_json_metadata


@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot, key_name="hash", value_name="exports_root")
class PackageDict(Dictionary[WorkPackageHash, SegmentRoot]):
    """Work Package hashes of each item reported (no more than CORE_COUNT)"""

    ...


@with_json_metadata(
    packages={"name":"reported"}
)
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
