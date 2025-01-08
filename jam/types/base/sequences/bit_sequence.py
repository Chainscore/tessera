from typing import Callable, Optional, Sequence, Tuple, Type, TypeVar, Union, List

from jam.types.base.boolean import Boolean
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from .base import BaseSequence

T = TypeVar('T', bound=Boolean)

class BitSequence(BaseSequence[Boolean]):
    """
    Fixed-length bit sequence implementation that supports codec operations.
    
    A BitSequence represents a fixed-length sequence of bits, where each bit
    is represented as a Boolean value. The sequence is encoded as a compact
    bit array.
    
    """
    
    length: int = 0
    
    def __init__(self, initial: Union[Sequence[Union[Boolean, int, bool]], bytes, bytearray, memoryview]):
        """
        Initialize bit sequence.
        
        Args:
            length: Fixed length of the sequence in bits
            initial: Optional initial values. Must match the fixed length.
                    All elements must be Boolean instances.
                    
        Raises:
            TypeError: If elements are not Boolean instances
            ValueError: If initial values don't match fixed length
        """
        super().__init__(codec=BitSequenceCodec(self.length))
        
        # Format different types into a list of Booleans
        __data = []
        if isinstance(initial, bytearray) or isinstance(initial, bytes) or isinstance(initial, memoryview):
            __data = [Boolean(bool(bit)) for bit in initial]
        else:
            for item in initial:
                if isinstance(item, Boolean):
                    __data.append(item)
                elif isinstance(item, int):
                    if item < 0 or item > 1:
                        raise TypeError(f"Invalid bit value: {item}")
                    __data.append(Boolean(bool(item)))
                elif isinstance(item, bool):
                    __data.append(Boolean(item))
        
        if len(__data) != self.length:
            raise ValueError(f"Initial values must have length {self.length}")

        self._data = __data
        
    def __setitem__(self, index: int, value: Boolean) -> None:
        """Set bit at index."""
        if not 0 <= index < self.length:
            raise IndexError(f"Index {index} out of range")
            
        if not isinstance(value, Boolean):
            raise TypeError("Value must be Boolean")
            
        self._data[index] = value

    def append(self, value: Boolean) -> None:
        """
        Append bit to end of sequence.
        
        Args:
            value: Value to append. Must be a Boolean instance.
            
        Raises:
            TypeError: If value is not a Boolean instance
            ValueError: If sequence is already at fixed length
        """
        if len(self._data) >= self.length:
            raise ValueError(f"Cannot append to sequence of fixed length {self.length}")
            
        if not isinstance(value, Boolean):
            raise TypeError("Value must be Boolean")
            
        self._data.append(value)

    def pop(self, index: int = -1) -> Boolean:
        """
        Remove and return bit at index.
        
        Args:
            index: Index of bit to remove
            
        Raises:
            ValueError: Sequence must maintain fixed length
        """
        raise ValueError("Cannot remove bits from fixed-length sequence")

    def insert(self, index: int, value: Boolean) -> None:
        """
        Insert bit at index.
        
        Args:
            index: Index to insert at
            value: Value to insert
            
        Raises:
            ValueError: Sequence must maintain fixed length
        """
        raise ValueError("Cannot insert into fixed-length sequence")

    def remove(self, value: Boolean) -> None:
        """
        Remove first occurrence of value.
        
        Args:
            value: Value to remove
            
        Raises:
            ValueError: Sequence must maintain fixed length
        """
        raise ValueError("Cannot remove from fixed-length sequence")

    def clear(self) -> None:
        """
        Clear all bits.
        
        Raises:
            ValueError: Sequence must maintain fixed length
        """
        raise ValueError("Cannot clear fixed-length sequence")

    def extend(self, values: Sequence[Boolean]) -> None:
        """
        Extend sequence with values.
        
        Args:
            values: Values to add
            
        Raises:
            ValueError: Sequence must maintain fixed length
        """
        raise ValueError("Cannot extend fixed-length sequence")

    def to_bytes(self) -> bytes:
        """
        Convert bit sequence to bytes.
        
        Returns:
            Bytes representation of the bit sequence
        """
        result = bytearray((len(self) + 7) // 8)
        for i, bit in enumerate(self._data):
            if bit.value:
                result[i // 8] |= 1 << (7 - (i % 8))
        return bytes(result)

    def from_bytes(self, data: bytes) -> None:
        """
        Set bits from bytes.
        
        Args:
            data: Bytes to set bits from
            
        Raises:
            ValueError: If bytes don't match sequence length
        """
        if len(data) * 8 < len(self):
            raise ValueError(f"Not enough bytes for {len(self)} bits")
            
        for i in range(len(self)):
            byte = data[i // 8]
            bit = (byte >> (7 - (i % 8))) & 1
            self._data[i] = Boolean(bit == 1)

    

def decodable_bit_sequence(length: int) -> Callable[[Type['BitSequence']], Type['BitSequence']]:
    """Decorator to make a class decodable as a bit sequence."""
    def decorator(cls: Type['BitSequence']) -> Type['BitSequence']:
        cls.length = length
        
        @staticmethod
        def decode_from(
            buffer: Union[bytes, bytearray, memoryview], 
            offset: int = 0
        ) -> Tuple['BitSequence', int]:
            bits, size = BitSequenceCodec.decode_from(length, buffer, offset)
            return cls(bits), size
        
        cls.decode_from = decode_from
        return cls
    return decorator