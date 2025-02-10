from typing import Any, Callable, Literal, Sequence, Tuple, Type, Union
from jam.types.base.bit import Bit
from jam.types.base.boolean import Boolean
from jam.types.base.sequences.array import Array
from jam.utils.byte_utils import Bytable, ByteUtils
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec

class BitArray(Array):
    """
    Fixed-length bit sequence implementation that supports codec operations.
    
    A BitSequence represents a fixed-length sequence of bits, where each bit
    is represented as a Boolean value. The sequence is encoded as a compact
    bit array.
    
    """
    _bit_order: Literal["msb", "lsb"] = "msb"

    def __init__(self, value: Bytable):
        """
        Initialize bit sequence.
        
        Args:
            value: Initial values. Must match the fixed length.
                    All elements must be Boolean instances.
                    
        Raises:
            TypeError: If elements are not Boolean instances
            ValueError: If initial values don't match fixed length
        """
        codec = BitSequenceCodec(bit_length=self._length, bit_order=self._bit_order)
        # If already a BitArray, just use it 
        if isinstance(value, BitArray) or (isinstance(value, Sequence) and all((isinstance(bit, (Bit, Boolean, bool))) for bit in value)):
            if not all(isinstance(bit, Bit) for bit in value):
                value = [Bit(bit) for bit in value]
            super().__init__(value, codec=codec)
            return
        
        # Format different types into a list of Booleans
        data: list[bool] = ByteUtils.bytes_to_bitarray(ByteUtils.to_bytes(value), bitorder=self._bit_order, target_length=self._length)
        super().__init__([Bit(bit) for bit in data], codec=codec)

    def __bytes__(self) -> bytes:
        return ByteUtils.bitarray_to_bytes([bool(bit) for bit in self.value])
    
    def __int__(self) -> int:
        return ByteUtils.bitarray_to_int([bool(bit) for bit in self.value])
    
    @classmethod
    def from_json(cls, data: Any) -> 'BitArray':
        return cls(data)

def decodable_bit_array(length: int, bitorder: Literal["msb", "lsb"]|None = "msb") -> Callable[[Type[BitArray]], Type[BitArray]]:
    """
    Extend existing decodable_array to be array of Bits
    """
    def decorator(cls: Type[BitArray]) -> Type[BitArray]:
        cls._length = length
        cls._element_type = Bit
        cls._bit_order = bitorder
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[BitArray, int]:
            value, size = BitSequenceCodec.decode_from(buffer, offset, length, bitorder)
            return cls(value), size
        
        cls.decode_from = decode_from
        
        return cls
    
    return decorator

@decodable_bit_array(8)
class Byte(BitArray):
    """
    A single byte value that supports codec operations. Array uses BitSequenceCodec.
    
    A Byte represents an 8-bit array that is encoded as
    a single byte.
    """
    
    def __repr__(self) -> str:
        return f"Byte(0x{bytes(self).hex()})"