from dataclasses import dataclass
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import HeaderHash, StateRoot
from jam.merklization.mountain_merkle import MMR
from jam.types.work.report import SegmentRootLookup
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde


@decodable_dataclass
@dataclass
class BlockHistory(Codable, JsonSerde):
    """Block history item"""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    reported: SegmentRootLookup


@decodable_vector(BlockHistory)
class Beta(Vector[BlockHistory]):
    """Beta state."""
    ...
