"""
Dictionary codec implementation for JAM protocol.

Implements encoding and decoding of key-value mappings according to the JAM specification.
Dictionaries are encoded as a length-prefixed sequence of key-value pairs, with pairs
sorted by encoded key bytes to ensure deterministic encoding.

Format:
    [Length_Tag: u8][Length_Data: varies][Pairs...]
    where each Pair is:
        [Encoded Key][Encoded Value]
"""

from typing import TypeVar, Generic, Dict as typing_Dict, Mapping, Union, Type, Optional, Tuple
import operator
from ..base import (
    Codec, CodecRegistry, EncodeError, DecodeError,
    check_buffer_size, ensure_size
)
from .vectors import VectorCodec

K = TypeVar('K')
V = TypeVar('V')

class DictionaryCodec(Codec[Mapping[K, V]], Generic[K, V]):
    """
    Codec for key-value mappings.
    
    Dictionaries are encoded as length-prefixed sequences of key-value pairs,
    sorted by encoded key bytes for deterministic encoding.
    """
    
    def __init__(
        self, 
        key_type: Type[K], 
        value_type: Type[V], 
        key_codec: Optional[Codec[K]] = None,
        value_codec: Optional[Codec[V]] = None
    ):
        """
        Initialize dictionary codec.
        
        Args:
            key_type: Type of dictionary keys
            value_type: Type of dictionary values
            key_codec: Optional specific codec for keys
            value_codec: Optional specific codec for values
            
        Raises:
            ValueError: If no codec found for key_type or value_type
        """
        self.key_type = key_type
        self.value_type = value_type
        
        # Get codecs for keys and values
        self.key_codec = key_codec or CodecRegistry.get(key_type)
        if self.key_codec is None:
            raise ValueError(
                f"No codec registered for key type {key_type.__name__}"
            )
        
        self.value_codec = value_codec or CodecRegistry.get(value_type)
        if self.value_codec is None:
            raise ValueError(
                f"No codec registered for value type {value_type.__name__}"
            )
            
        # Create codec for sequence of key-value pairs
        # This gives us length prefix encoding for free
        PairType = Tuple[key_type, value_type]  
        self.pair_codec = VectorCodec(PairType)

    def _encode_pair(
        self, key: K, value: V, buffer: bytearray, offset: int
    ) -> Tuple[bytes, int]:
        """
        Encode a single key-value pair into buffer.
        
        Args:
            key: Key to encode
            value: Value to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (key_bytes for sorting, bytes written)
            
        Raises:
            EncodeError: If key/value invalid or buffer too small
        """
        if not isinstance(key, self.key_type):
            raise EncodeError(
                0, 0,
                f"Invalid key type: expected {self.key_type.__name__}, "
                f"got {type(key).__name__}"
            )
            
        if not isinstance(value, self.value_type):
            raise EncodeError(
                0, 0,
                f"Invalid value type: expected {self.value_type.__name__}, "
                f"got {type(value).__name__}"
            )
            
        # Encode key
        if self.key_codec is None:
            raise EncodeError(0, 0, "Key codec is None")
            
        key_bytes = self.key_codec.encode(key)
        written = self.key_codec.encode_into(key, buffer, offset)
        
        # Encode value
        if self.value_codec is None:
            raise EncodeError(0, 0, "Value codec is None")
            
        value_written = self.value_codec.encode_into(value, buffer, offset + written)
        
        return key_bytes, written + value_written

    def encode_size(self, value: Mapping[K, V]) -> int:
        """
        Calculate number of bytes needed to encode dictionary.
        
        Args:
            value: Dictionary to encode
            
        Returns:
            Number of bytes needed
            
        Raises:
            EncodeError: If dictionary contains invalid types
        """
        if not isinstance(value, (dict, Mapping)):
            raise EncodeError(
                0, 0,
                f"Expected dict or Mapping, got {type(value).__name__}"
            )
            
        if self.key_codec is None or self.value_codec is None:
            raise EncodeError(0, 0, "Key or value codec is None")
        
        # Calculate size for length prefix
        pairs = sorted(
            value.items(),
            key=lambda x: self.key_codec.encode(x[0]) # type: ignore
        )
        
        # Calculate size for all pairs
        pairs_size = sum(
            self.key_codec.encode_size(k) + self.value_codec.encode_size(v)
            for k, v in pairs
        )
        
        # Get length prefix size from pair codec
        total_size = self.pair_codec.encode_size(pairs)
        
        return total_size

    def encode_into(self, value: Mapping[K, V], buffer: bytearray, offset: int = 0) -> int:
        """
        Encode dictionary into buffer.
        
        Args:
            value: Dictionary to encode
            buffer: Target buffer
            offset: Starting position in buffer
            
        Returns:
            Number of bytes written
            
        Raises:
            EncodeError: If dictionary invalid or buffer too small
        """
        if not isinstance(value, (dict, Mapping)):
            raise EncodeError(
                0, 0,
                f"Expected dict or Mapping, got {type(value).__name__}"
            )
            
        total_size = self.encode_size(value)
        check_buffer_size(buffer, total_size, offset)
        
        try:
            # Get sorted pairs by encoded key
            temp_buffer = bytearray(1024)  # Buffer for temporary key encoding
            pairs_with_key_bytes = []
            
            for key, val in value.items():
                key_bytes, _ = self._encode_pair(key, val, temp_buffer, 0)
                pairs_with_key_bytes.append((key_bytes, (key, val)))
                
            pairs = [p[1] for p in sorted(pairs_with_key_bytes)]
            
            # Use pair codec to encode length and pairs
            return self.pair_codec.encode_into(pairs, buffer, offset)
            
        except EncodeError as e:
            raise EncodeError(0, 0, f"Failed to encode dictionary: {str(e)}")

    def decode_from(
        self, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[typing_Dict[K, V], int]:
        """
        Decode dictionary from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting position in buffer
            
        Returns:
            Tuple of (decoded dict, bytes read)
            
        Raises:
            DecodeError: If buffer too small or invalid encoding
        """
        try:
            # Use pair codec to decode length and pairs
            pairs, size = self.pair_codec.decode_from(buffer, offset)
            
            # Convert to dictionary
            result = {}
            for key, value in pairs:
                if key in result:
                    raise DecodeError(
                        0, 0,
                        f"Duplicate key in dictionary: {key}"
                    )
                result[key] = value
                
            return result, size
            
        except DecodeError as e:
            raise DecodeError(0, 0, f"Failed to decode dictionary: {str(e)}")


class Dict(Generic[K, V]):
    """Type alias helper for dictionaries."""
    
    def __class_getitem__(cls, types: Tuple[Type[K], Type[V]]) -> DictionaryCodec[K, V]:
        """
        Create dictionary codec through type syntax.
        
        Example:
            codec = Dict[str, int]  # Creates codec for Dict[str, int]
        """
        if not isinstance(types, tuple) or len(types) != 2:
            raise TypeError("Dict type requires [key_type, value_type]")
            
        key_type, value_type = types
        return DictionaryCodec(key_type, value_type)


def make_dict_codec(
    key_type: Type[K], value_type: Type[V]
) -> DictionaryCodec[K, V]:
    """
    Create dictionary codec for given key and value types.
    
    Args:
        key_type: Type of dictionary keys
        value_type: Type of dictionary values
        
    Returns:
        DictionaryCodec instance
        
    Example:
        codec = make_dict_codec(str, int)
    """
    return DictionaryCodec(key_type, value_type)


def register_dict_type(dict_type: Type) -> None:
    """
    Register codec for a specific dictionary type.
    
    Args:
        dict_type: Dictionary type to register (e.g., Dict[str, int])
        
    Example:
        register_dict_type(Dict[str, int])
    """
    from typing import get_args, get_origin
    
    if get_origin(dict_type) in (typing_Dict, Dict):
        key_type, value_type = get_args(dict_type)
        CodecRegistry.register(dict_type, make_dict_codec(key_type, value_type))