from typing import Any, Sequence
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.byte_utils import ByteUtils, Bytable
from jam.types.base.sequences.bytes.bit_array import Byte


@decodable_vector(Byte)
class Bytes(Vector[Byte]):
    """Variable-length byte sequence type."""

    def __init__(self, value: Bytable):
        """
        Initialize Bytes.

        Args:
            value: Bytable which is either int, bytes, str, bytearray, memoryview, Sequence[Byte]
        """
        if isinstance(value, Sequence) and all(isinstance(val, Byte) for val in value):
            super().__init__(value)
            return
        data: list[Byte] = [Byte(b) for b in ByteUtils.to_bytes(value)]
        super().__init__(data)

    def hex(self) -> str:
        """Get hex representation of Bytes."""
        return bytes(self).hex()

    @classmethod
    def from_json(cls, data: Any) -> "Bytes":
        """Create from JSON representation."""
        return cls(data)

    def to_json(self) -> str:
        return f"0x{self.hex()}"
