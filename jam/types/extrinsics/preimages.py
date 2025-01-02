"""Preimage-related extrinsic types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence, Union

from jam.types.base.integers import U32
from jam.types.base.bytes import Bytes
from jam.types.base.vector import Vector
from jam.utils.codec.base import Codable
from jam.types.protocol.core import ServiceId
from jam.utils.codec.composite.vectors import VectorCodec

@dataclass
class Preimage(Codable):
    """Preimage structure."""
    requester: ServiceId
    blob: Bytes

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.requester, self.blob]

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
        requester, size = ServiceId.decode_from(buffer, current_offset)
        current_offset += size
        blob, size = Bytes.decode_from(buffer, current_offset)
        current_offset += size
        return Preimage(requester, blob), current_offset - offset

class PreimagesExtrinsic(Vector[Preimage]):
    """Sequence of preimages."""
    def __init__(self, preimages: List[Preimage]):
        super().__init__(preimages) 

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        preimages, size = VectorCodec.decode_from(Preimage, buffer, offset)
        return PreimagesExtrinsic(preimages), size
