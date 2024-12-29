"""Dictionary implementation"""
from typing import Generic, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union

from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.dictionaries import DictionaryCodec

K = TypeVar('K')
V = TypeVar('V')

class Dictionary(Generic[K, V], Codable, Mapping[K, V]):
    """
    Dictionary implementation that supports codec operations.
    
    The dictionary stores key-value pairs and supports codec operations
    for serialization/deserialization.
    """
    
    def __init__(self, initial: Optional[Mapping[K, V]] = None):
        """
        Initialize dictionary.
        
        Args:
            initial: Optional initial key-value pairs
        """
        self._data = {}
        if initial is not None:
            self._data.update(initial)

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dictionary):
            return False
        return self._data == other._data

    def __repr__(self) -> str:
        return f"Dict(data={self._data})"

    @staticmethod
    def decode_from(
        key_type: Type[Codable[K]],
        value_type: Type[Codable[V]],
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple[Mapping[K, V], int]:
        """
        Decode dictionary from buffer.
        
        Args:
            key_type: Type of dictionary keys
            value_type: Type of dictionary values
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded dictionary, bytes read)
        """
        codec = DictionaryCodec()
        value, size = codec.decode_from(key_type, value_type, buffer, offset)
        return Dictionary(value), size 
