"""Refine context types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence

from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import (
    HeaderHash, StateRoot, BeefyRoot, OpaqueHash
)
from jam.types.protocol.core import TimeSlot

@decodable_vector(OpaqueHash)
class OpaqueHashes(Vector[OpaqueHash]): pass

@dataclass
class RefineContext(Codable):
    """Refine context structure."""
    anchor: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    lookup_anchor: HeaderHash
    lookup_anchor_slot: TimeSlot
    prerequisites: Vector[OpaqueHash]

    def enc_sequence(self) -> Sequence[Codable]:
        sequence: List[Codable] = [
            self.anchor,
            self.state_root,
            self.beefy_root,
            self.lookup_anchor,
            self.lookup_anchor_slot,
            self.prerequisites
        ]
        return sequence

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        anchor, size = HeaderHash.decode_from(buffer, current_offset)
        current_offset += size
        state_root, size = StateRoot.decode_from(buffer, current_offset)
        current_offset += size
        beefy_root, size = BeefyRoot.decode_from(buffer, current_offset)
        current_offset += size
        lookup_anchor, size = HeaderHash.decode_from(buffer, current_offset)
        current_offset += size
        lookup_anchor_slot, size = TimeSlot.decode_from(buffer, current_offset)
        current_offset += size
        prerequisites, size = OpaqueHashes.decode_from(buffer, current_offset)
        current_offset += size

        return RefineContext(
            anchor,
            state_root,
            beefy_root,
            lookup_anchor,
            lookup_anchor_slot,
            Vector(prerequisites)
        ), current_offset - offset 