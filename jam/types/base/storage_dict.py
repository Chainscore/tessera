from typing import (
    Generic,
    Mapping,
    Optional,
    Self,
    Tuple,
    Type,
    TypeVar,
    Union,
    Dict,
    Iterator,
    ItemsView,
    KeysView,
    ValuesView,
    Any,
    Sequence,
)

from jam.storage.db.kv import KVStore
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dictionaries import DictionaryCodec
from jam.utils.json import JsonSerde

K = TypeVar("K", bound=Codable)
V = TypeVar("V", bound=Codable)


class StorageDict(Generic[K, V], Codable, Mapping[K, V], JsonSerde):
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

    key_type: Type[K]
    value_type: Type[V]

    db: KVStore

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

        db = KVStore(settings)
        if initial is not None:
            self.value.update(initial)

    def construct_key(self, key: bytes) -> bytes:
        raise TypeError(f"{self.__class__.__name__} has not implemented construct_key() function. Unable to construct key")

    def __getitem__(self, key: K) -> V:
        """Get value for key."""
        return self.value[key]

    def __setitem__(self, key: K, value: V) -> None:
        """Set value for key."""
        self.value[key] = value

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

    def to_json(self) -> Dict[Any, Any]:
        """Convert to JSON representation."""
        return {k.to_json(): v.to_json() for k, v in self.items()}

    @classmethod
    def from_json(cls: Type[Self], data: Dict[Any, Any] | Sequence[Any]) -> Self:
        """Create instance from JSON representation."""
        if not isinstance(data, dict):
            raise ValueError("Dictionary: JSON representation must be a dictionary")
        return cls(
            {
                cls.key_type.from_json(k): cls.value_type.from_json(v)
                for k, v in data.items()
            }
        )


def decodable_dictionary(
    key_type: Type[K], value_type: Type[V]
) -> Type[Dictionary[K, V]]:
    def decorator(cls: Type[Dictionary[K, V]]) -> Type[Dictionary[K, V]]:
        cls.key_type = key_type
        cls.value_type = value_type

        @staticmethod
        def decode_from(
            buffer: Union[bytes, bytearray, memoryview], offset: int = 0
        ) -> Tuple["Dictionary[K, V]", int]:
            value, size = DictionaryCodec.decode_from(
                key_type, value_type, buffer, offset
            )
            return Dictionary(value), size

        cls.decode_from = decode_from
        return cls

    return decorator
