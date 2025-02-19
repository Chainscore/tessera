from enum import Enum as OGEnum
from typing import Tuple, Type, Union, Any, TypeVar, cast
from jam.types.base.integers.fixed import U8
from jam.utils.codec.codable import Codable
from jam.utils.json import JsonSerde
from jam.utils.json.serde import JsonDeserializationError

T = TypeVar("T", bound="Enum")


class Enum(Codable, JsonSerde, OGEnum):
    """Decodable Enum type - Extending the built-in Enum type to add encoding and decoding methods

    How to use it:
    >>> class MyEnum(Enum):
    >>>     A = 1
    >>>     B = 2
    >>>     C = 3
    >>>
    >>> value = MyEnum.A
    >>> encoded = value.encode()
    >>> decoded, bytes_read = MyEnum.decodeFrom(encoded)
    >>> assert decoded == value
    >>> assert bytes_read == 1
    >>>
    >>> assert MyEnum.from_json(1,) == MyEnum.A
    >>> assert MyEnum.from_json("A",) == MyEnum.A
    """

    def encode_size(self) -> int:
        """Return the size in bytes needed to encode this enum value"""
        return 1

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode this enum value into the given buffer at the given offset

        Args:
            buffer: The buffer to encode into
            offset: The offset to start encoding at

        Returns:
            The number of bytes written

        Raises:
            ValueError: If the enum has too many variants to encode in a byte
        """
        # Get the index of the enum value in all enums
        # Encode the index as a byte
        all_enums = self.__class__._member_names_
        index = all_enums.index(self.name)
        if index > 255:
            raise ValueError("Enum index is too large to encode into a single byte")
        return U8(index).encode_into(buffer, offset)

    @classmethod
    def decodeFrom(
        cls: Type[T], data: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[T, int]:
        """Decode an enum value from the given buffer at the given offset

        Args:
            data: The buffer to decode from
            offset: The offset to start decoding at

        Returns:
            A tuple of (decoded enum value, number of bytes read)

        Raises:
            ValueError: If the encoded index is invalid
        """
        # Decode the byte (index of enum) into an Enum
        # Return the enum value
        index, bytes_read = U8.decode_from(data, offset)
        value = cast(T, cls._member_map_[cls._member_names_[index]])
        return value, bytes_read

    @classmethod
    def from_json(cls: Type[T], data: Any) -> T:
        """Convert a JSON value to an enum value

        Args:
            data: The JSON value (either the enum value or name)

        Returns:
            The corresponding enum value

        Raises:
            JsonDeserializationError: If the value is invalid
        """
        for v in cls.__members__.values():
            if v._value_ == data or v._name_ == data:
                return cast(T, v)
        raise JsonDeserializationError(f"Invalid value: {data}")

    def to_json(self) -> Any:
        """Convert this enum value to a JSON value

        Returns:
            The enum's value for JSON serialization
        """
        return self._value_


def decodable_enum(cls: Type[Enum]) -> Type[Enum]:
    """Decorator to make an enum class decodable

    Args:
        cls: The enum class to make decodable

    Returns:
        The decorated enum class with decode_from method added
    """

    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Enum, int]:
        return cls.decodeFrom(buffer, offset)

    cls.decode_from = decode_from
    return cls
