# Fixed-size array types
from typing import Any, List, Tuple
from jam.types.base.array import Array
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.codec.composite.arrays import ArrayCodec

class EntropyBuffer(Array[OpaqueHash]):
    """Fixed-size array of entropy values with size 4."""
    
    def __init__(self, items: List[OpaqueHash]):
        super().__init__(4, items)

    @classmethod
    def decode_from(cls, buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        return ArrayCodec.decode_from(4, OpaqueHash, buffer, offset)
