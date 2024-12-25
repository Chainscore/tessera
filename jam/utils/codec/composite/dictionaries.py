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

from jam.utils.codec.primitives.integers import general_codec
from jam.utils.codec.utils import check_buffer_size
from ..base import (
    Codec, EncodeError, DecodeError,
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
        key_codec: Codec[K],
        value_codec: Codec[V]
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
        self.key_codec = key_codec
        self.value_codec = value_codec

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
        total_size = general_codec.encode_size(len(pairs)) + pairs_size
        
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
            temp_buffer = bytearray(1024)
            pairs_with_key_bytes = []
            
            for key, val in value.items():
                key_bytes, _ = self._encode_pair(key, val, temp_buffer, 0)
                pairs_with_key_bytes.append((key_bytes, (key, val)))
                
            pairs = [p[1] for p in sorted(pairs_with_key_bytes)]
            
            # Encode length prefix using VectorCodec's length encoding scheme
            len_encoded = general_codec.encode(len(pairs))
            buffer[offset:offset+len(len_encoded)] = len_encoded
            current_offset = offset + len(len_encoded)
            
            # Encode each pair directly
            for key, val in pairs:
                written = self.key_codec.encode_into(key, buffer, current_offset)
                current_offset += written
                written = self.value_codec.encode_into(val, buffer, current_offset)
                current_offset += written
                
            return current_offset - offset
            
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
            # Decode length prefix using VectorCodec's length decoding scheme
            length, length_size = general_codec.decode_from(buffer, offset)
            current_offset = offset + length_size
            
            # Decode pairs
            result = {}
            for _ in range(length):
                # Decode key
                key, key_size = self.key_codec.decode_from(buffer, current_offset)
                current_offset += key_size
                
                # Decode value
                value, value_size = self.value_codec.decode_from(buffer, current_offset)
                current_offset += value_size
                
                if key in result:
                    raise DecodeError(0, 0, f"Duplicate key in dictionary: {key}")
                result[key] = value
                
            return result, current_offset - offset
            
        except DecodeError as e:
            raise DecodeError(0, 0, f"Failed to decode dictionary: {str(e)}")