from typing import (
    Generic, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union, Dict,
    Iterator, ItemsView, KeysView, ValuesView
)

from jam.utils.codec.base import Codec, Codable
from jam.utils.codec.composite.dictionaries import DictionaryCodec

K = TypeVar('K', bound=Codable)
V = TypeVar('V', bound=Codable)

class Dictionary(Generic[K, V], Codable, Mapping[K, V]):
    """
    Dictionary implementation that supports codec operations.
    
    A dictionary that maps Codable keys to Codable values, providing both standard
    dictionary operations and codec functionality for serialization/deserialization.
    
    Examples:
        >>> from jam.types.base.string import String
        >>> from jam.types.base.integers import Int
        >>> d = Dictionary({String("key"): Int(42)})
        >>> d[String("key")]
        Int(42)
        >>> encoded = d.encode()
        >>> decoded, _ = Dictionary.decode_from(String, Int, encoded)
        >>> decoded == d
        True
    """
    
    def __init__(self, initial: Optional[Mapping[K, V]] = None):
        """
        Initialize dictionary.
        
        Args:
            initial: Optional initial key-value pairs
            
        Raises:
            TypeError: If any key or value is not Codable
        """
        if initial is not None:
            for key, value in initial.items():
                if not isinstance(key, Codable) or not isinstance(value, Codable):
                    raise TypeError("Dictionary keys and values must be Codable")
                    
        super().__init__(codec=DictionaryCodec())
        self.value: Dict[K, V] = {}
        if initial is not None:
            self.value.update(initial)

    def __getitem__(self, key: K) -> V:
        """Get value for key."""
        return self.value[key]

    def __iter__(self) -> Iterator[K]:
        """Iterate over keys."""
        return iter(self.value)

    def __len__(self) -> int:
        """Get number of items."""
        return len(self.value)

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if not isinstance(other, Dictionary):
            return False
        return self.value == other.value

    def __repr__(self) -> str:
        """Get string representation."""
        items = [f"{k!r}: {v!r}" for k, v in self.value.items()]
        return f"Dictionary({{{', '.join(items)}}})"

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """
        Get value for key, returning default if key not found.
        
        Args:
            key: Key to look up
            default: Value to return if key not found
            
        Returns:
            Value for key or default
        """
        return self.value.get(key, default)

    def items(self) -> ItemsView[K, V]:
        """Get view of (key, value) pairs."""
        return self.value.items()

    def keys(self) -> KeysView[K]:
        """Get view of keys."""
        return self.value.keys()

    def values(self) -> ValuesView[V]:
        """Get view of values."""
        return self.value.values()

    @staticmethod
    def decode_from(
        key_type: Type[K],
        value_type: Type[V],
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple['Dictionary[K, V]', int]:
        """
        Decode dictionary from buffer.
        
        Args:
            key_type: Type of dictionary keys (must be Codable)
            value_type: Type of dictionary values (must be Codable)
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded dictionary, bytes read)
            
        Raises:
            DecodeError: If buffer is invalid or too short
            TypeError: If key_type or value_type is not Codable
        """
        if not issubclass(key_type, Codable) or not issubclass(value_type, Codable):
            raise TypeError("Dictionary key and value types must be Codable")
            
        value, size = DictionaryCodec.decode_from(key_type, value_type, buffer, offset)
        return Dictionary(value), size 
