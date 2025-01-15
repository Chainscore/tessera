from collections.abc import Sequence
from typing import Literal, Tuple, Union
from jam.types.base.integers.fixed import U8
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.integers import IntegerCodec

Bytable = Union[int, bytes, str, bytearray, memoryview, U8, Sequence[0|1]]

class Byte(Codable[int]):
    """
    A single byte value that supports codec operations.
    
    A Byte represents an integer in the range [0, 255] that is encoded as
    a single byte.
    
    Examples:
        >>> b = Byte(42)
        >>> assert b.value == 42
        >>> encoded = b.encode()
        >>> decoded, _ = Byte.decode_from(encoded)
        >>> assert decoded == b
    """

    def __init__(self, value: Bytable):
        """
        Initialize byte.
        
        Args:
            value: Integer value in range [0, 255]
            
        Raises:
            TypeError: If value is not an integer
            ValueError: If value is out of range
        """
        # Wrap value if it's not a Byte
        if isinstance(value, str):
            if value.startswith('0x'):
                value = int(value[2:], 16)
            else:
                value = int(value, 16)
        if isinstance(value, Byte) or isinstance(value, U8):
            value = value.value
        elif isinstance(value, bytes) or isinstance(value, bytearray) or isinstance(value, memoryview):
            value = int.from_bytes(value)
        elif isinstance(value, U8):
            value = value.value
        elif isinstance(value, Sequence):
            value = Byte.from_bit_array(value).value
        elif isinstance(value, int):
            pass
        else:
            raise TypeError(f"Value ${type(value)} must be ${Bytable}")
        
        if not 0 <= value <= 255:
            raise ValueError(f"Value {value} must be in range [0, 255]")
            
        self.value = value

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Byte(0x{self.value:02x})"

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, Byte):
            return self.value == other.value
        if isinstance(other, Bytable):
            return self == Byte(other)
        
        if isinstance(other, int):
            return 0 <= other <= 255 and self.value == other
        return False

    def __int__(self) -> int:
        """Convert to integer."""
        return self.value

    def __index__(self) -> int:
        """Convert to integer for indexing."""
        return self.value
    
    def encode_size(self) -> int:
        """Get size of encoded byte."""
        return 1
    
    def encode_into(self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> int:
        """Encode byte into buffer."""
        return IntegerCodec(1).encode_into(self.value, buffer, offset)
    
    def to_bit_array(self, bitorder: Literal["big", "little"] = "big") -> Sequence[0|1]:
        """Get an array of bits"""
        if bitorder == "big":
            return [(self.value >> i) & 1 for i in range(7, -1, -1)]
        else:
            return [(self.value >> i) & 1 for i in range(0, 8)]
    
    @staticmethod
    def from_bit_array(bits: Sequence[0|1], bitorder: Literal["big", "little"] = "big") -> 'Byte':
        """Convert an array of bits to a byte value
        
        Args:
            bits: Sequence of 8 bits (0 or 1)
            
        Returns:
            Byte: New byte object with the value from bits
            
        Raises:
            ValueError: If bits sequence is not exactly 8 bits or contains invalid values
        """
        # Validate length
        if len(bits) != 8:
            # Add leading zeros if necessary
            bits = [0] * (8 - len(bits)) + bits
        # Validate bits are only 0 or 1
        if not all(bit in (0, 1) for bit in bits):
            raise ValueError("Bits must be 0 or 1")
        
        if bitorder == "big":
            # Convert bit array to integer
            value = sum(bit << (7-i) for i, bit in enumerate(bits))
        else: 
            value = sum(bit << i for i, bit in enumerate(bits))
        
        # Create new byte object with the calculated value
        return Byte(value)
    
    def set_bits(self, position: int|slice, value: int | Sequence[0 | 1], bitorder: Literal["big", "little"] = "big") -> 'Byte':
        bit_arr = self.to_bit_array(bitorder)
        if isinstance(position, slice):
            bit_arr[position] = value
        else:
            bit_arr[position] = value
        self.value = self.from_bit_array(bit_arr).value
        return self

    def __bytes__(self) -> bytes:
        return self.value.to_bytes(1, "big")

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple['Byte', int]:
        """
        Decode byte from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded byte, bytes read)
            
        Raises:
            DecodeError: If buffer is invalid or too short
        """
        value, size = IntegerCodec(1).decode_from(1, buffer, offset)
        if not 0 <= value <= 255:
            raise ValueError(f"Decoded value {value} is out of range [0, 255]")
        return Byte(value), size 