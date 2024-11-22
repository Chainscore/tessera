"""
Tuple codec implementation for JAM protocol.

Implements encoding and decoding of fixed-size tuples according to the JAM specification.
Tuples are encoded by concatenating their encoded elements in order.
Each element can be of a different type, and the types are known at encoding/decoding time.
"""

from typing import (
    TypeVar, Generic, Tuple as PyTuple, Union, Sequence,
    Type, get_args, get_origin
)
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)

T = TypeVar('T')

class TupleCodec(Codec[PyTuple]):
    """
    Codec for fixed-size tuples.
    
    Tuples are encoded by concatenating their encoded elements in order.
    Each element can be of a different type and uses its own codec.
    """
    
    def __init__(self, types: Sequence[Type]):
        """
        Initialize tuple codec.
        
        Args:
            types: Sequence of types for each tuple element
            
        Raises:
            ValueError: If no codec found for any element type
        """
        self.types = types
        
        # Get codecs for each element type
        self.codecs = []
        for idx, type_ in enumerate(types):
            codec = CodecRegistry.get(type_)
            if codec is None:
                raise ValueError(
                    f"No codec registered for type {type_.__name__} "
                    f"at position {idx}"
                )
            self.codecs.append(codec)

    def encode_size(self, value: PyTuple) -> int:
        """
        Calculate number of bytes needed to encode tuple.
        
        Args:
            value: Tuple to encode
            
        Returns:
            Number of bytes needed
            
        Raises:
            EncodeError: If tuple length doesn't match expected or contains wrong types
        """
        if not isinstance(value, tuple):
            raise EncodeError(
                len(self.types), 0,
                f"Expected tuple, got {type(value)}"
            )
            
        if len(value) != len(self.types):
            raise EncodeError(
                len(self.types), len(value),
                f"Tuple length mismatch: expected {len(self.types)}, "
                f"got {len(value)}"
            )
            
        total_size = 0
        for idx, (item, expected_type, codec) in enumerate(
            zip(value, self.types, self.codecs)
        ):
            if not isinstance(item, expected_type):
                raise EncodeError(
                    0, 0,
                    f"Type mismatch at position {idx}: "
                    f"expected {expected_type.__name__}, "
                    f"got {type(item).__name__}"
                )
            total_size += codec.encode_size(item)
            
        return total_size

    def encode_into(self, value: PyTuple, buffer: bytearray, offset: int = 0) -> int:
        """
        Encode tuple into buffer.
        
        Args:
            value: Tuple to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If tuple is invalid or buffer too small
        """
        # Validate tuple and calculate size
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        # Encode each element
        current_offset = offset
        for item, codec in zip(value, self.codecs):
            written = codec.encode_into(item, buffer, current_offset)
            current_offset += written
            
        return current_offset - offset

    def decode_from(
        self, buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> PyTuple[PyTuple, int]:
        """
        Decode tuple from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded tuple, bytes read)
            
        Raises:
            DecodeError: If buffer is too small or invalid encoding
        """
        current_offset = offset
        result = []
        
        try:
            for idx, codec in enumerate(self.codecs):
                item, size = codec.decode_from(buffer, current_offset)
                result.append(item)
                current_offset += size
        except DecodeError as e:
            raise DecodeError(
                0, 0,
                f"Failed to decode tuple element {len(result)}: {str(e)}"
            )
            
        return tuple(result), current_offset - offset


def make_tuple_codec(*types: Type) -> TupleCodec:
    """
    Create tuple codec for given element types.
    
    Args:
        *types: Types of tuple elements in order
        
    Returns:
        TupleCodec instance
        
    Example:
        codec = make_tuple_codec(int, str, bool)
    """
    return TupleCodec(types)


# Type alias helper for tuples
class Tuple(Generic[T]):
    """Type alias helper for tuples."""
    
    def __class_getitem__(cls, key: Union[Type, PyTuple[Type, ...]]) -> TupleCodec:
        """
        Create tuple codec through type syntax.
        
        Example:
            codec = Tuple[int, str, bool]  # Creates codec for Tuple[int, str, bool]
        """
        if not isinstance(key, tuple):
            key = (key,)
            
        return make_tuple_codec(*key)


def register_tuple_type(tuple_type: Type) -> None:
    """
    Register codec for a specific tuple type.
    
    Args:
        tuple_type: Tuple type to register (e.g., Tuple[int, str])
        
    Example:
        register_tuple_type(Tuple[int, str])
    """
    if get_origin(tuple_type) is tuple:
        args = get_args(tuple_type)
        CodecRegistry.register(tuple_type, make_tuple_codec(*args))