from typing import Callable, Optional, Sequence, Tuple, Type, TypeVar, Union

from jam.utils.codec.composite.arrays import ArrayCodec
from jam.types.base.byte import Byte
from .base import BaseSequence

T = TypeVar('T', bound=Byte)

class ByteArray(BaseSequence[Byte]):
    """
    Fixed-length byte array implementation that supports codec operations.
    
    A ByteArray represents a fixed-length sequence of bytes, where each byte
    is a value in the range [0, 255]. The sequence is encoded directly
    as bytes.
    
    Examples:
        >>> arr = ByteArray(4, [Byte(0x01), Byte(0x02), Byte(0x03), Byte(0x04)])
        >>> assert len(arr) == 4
        >>> assert arr[0] == Byte(0x01)
        >>> encoded = arr.encode()
        >>> decoded, _ = ByteArray.decode_from(4, encoded)
        >>> assert decoded == arr
    """
    
    length: int = 0
    
    def __init__(self, initial: Sequence[Union[Byte, int]] ):
        """
        Initialize byte array.
        
        Args:
            length: Fixed length of the array in bytes
            initial: Optional initial values. Must match the fixed length.
                    Values can be Byte instances or integers in range [0, 255].
                    
        Raises:
            TypeError: If elements are not valid bytes
            ValueError: If initial values don't match fixed length or are out of range
        """
        super().__init__(codec=ArrayCodec(self.length))
        self._element_type = Byte
        
        if len(initial) != self.length:
            raise ValueError(f"Initial values must have length {self.length}")
        
        self._data = [Byte(0)] * self.length
        for item, i in zip(initial, range(self.length)):
            if isinstance(item, int):
                self._data[i] = Byte(item)
            else:
                self._data[i] = item
        

    def __setitem__(self, index: int, value: Union[Byte, int]) -> None:
        """Set byte at index."""
        if not 0 <= index < self.length:
            raise IndexError(f"Index {index} out of range")
            
        if isinstance(value, int):
            value = Byte(value)
            
        if not isinstance(value, Byte):
            raise TypeError("Value must be Byte or integer")
            
        self._data[index] = value

    def append(self, value: Union[Byte, int]) -> None:
        """
        Append byte to end of array.
        
        Args:
            value: Value to append. Must be a Byte instance or integer in range [0, 255].
            
        Raises:
            TypeError: If value is not a valid byte
            ValueError: If array is at fixed length
        """
        if len(self._data) >= self.length:
            raise ValueError(f"Cannot append to array of fixed length {self.length}")
            
        if isinstance(value, int):
            value = Byte(value)
            
        if not isinstance(value, Byte):
            raise TypeError("Value must be Byte or integer")
            
        self._data.append(value)

    def pop(self, index: int = -1) -> Byte:
        """
        Remove and return byte at index.
        
        Args:
            index: Index of byte to remove
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot remove bytes from fixed-length array")

    def insert(self, index: int, value: Union[Byte, int]) -> None:
        """
        Insert byte at index.
        
        Args:
            index: Index to insert at
            value: Value to insert
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot insert into fixed-length array")

    def remove(self, value: Union[Byte, int]) -> None:
        """
        Remove first occurrence of value.
        
        Args:
            value: Value to remove
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot remove from fixed-length array")

    def clear(self) -> None:
        """
        Clear all bytes.
        
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot clear fixed-length array")

    def extend(self, values: Sequence[Union[Byte, int]]) -> None:
        """
        Extend array with values.
        
        Args:
            values: Values to add
            
        Raises:
            ValueError: Array must maintain fixed length
        """
        raise ValueError("Cannot extend fixed-length array")

    def to_bytes(self) -> bytes:
        """
        Convert byte array to bytes.
        
        Returns:
            Bytes representation of the array
        """
        return bytes(x.value for x in self._data)

    def from_bytes(self, data: bytes) -> None:
        """
        Set bytes from bytes object.
        
        Args:
            data: Bytes to set
            
        Raises:
            ValueError: If bytes don't match array length
        """
        if len(data) != self.length:
            raise ValueError(f"Data must have length {self.length}")
            
        self._data = [Byte(x) for x in data]

    @classmethod
    def decode_from(
        cls,
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple['ByteArray', int]:
        if cls.codec is None:
            raise ValueError("Codec not set")
        return cls.codec.decode_from(buffer, offset)

    def __eq__(self, other: object) -> bool:
        """
        Compare for equality with another object.
        
        Supports comparison with:
        - Other ByteArray instances
        - bytes/bytearray/memoryview objects
        - Sequences of integers
        
        Args:
            other: Object to compare with
            
        Returns:
            True if objects are equal, False otherwise
        """
        if isinstance(other, ByteArray):
            return len(self) == len(other) and self.to_bytes() == other.to_bytes()
        elif isinstance(other, (bytes, bytearray, memoryview)):
            return len(self) == len(other) and self.to_bytes() == bytes(other)
        elif isinstance(other, list):
            try:
                return len(self) == len(other) and all(
                    self[i] == other[i] for i in range(len(self))
                )
            except (TypeError, IndexError, AttributeError):
                return False
        return False

def decodable_byte_array(length: int) -> Callable[[Type['ByteArray']], Type['ByteArray']]:
    """Decorator to make a class decodable as a fixed-length byte array."""
    def decorator(cls: Type['ByteArray']) -> Type['ByteArray']:
        cls.length = length
        
        @staticmethod
        def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple['ByteArray', int]:
            value, size = ArrayCodec.decode_from(length, Byte, buffer, offset)
            return cls(value), size
        
        cls.decode_from = decode_from
        return cls
    return decorator

@decodable_byte_array(8)
class ByteArray8(ByteArray): pass

@decodable_byte_array(16)
class ByteArray16(ByteArray): pass

@decodable_byte_array(32)
class ByteArray32(ByteArray): pass

@decodable_byte_array(64)
class ByteArray64(ByteArray): pass

@decodable_byte_array(96)
class ByteArray96(ByteArray): pass

@decodable_byte_array(128)
class ByteArray128(ByteArray): pass

@decodable_byte_array(144)
class ByteArray144(ByteArray): pass

@decodable_byte_array(256)
class ByteArray256(ByteArray): pass

@decodable_byte_array(784)
class ByteArray784(ByteArray): pass