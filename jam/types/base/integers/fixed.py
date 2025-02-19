import math
from typing import Callable, Union, Any, Tuple, TypeVar, Type
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import IntegerCodec
from .base import BaseInteger

T = TypeVar("T", bound="BaseInteger")


class FixedInt(BaseInteger, Codable):
    """Fixed-width integer type."""

    byte_size: int = 0
    has_sign = False

    def __init__(self, value: Union[int, "BaseInteger"]):
        super().__init__(value)
        self._validate(self.value)
        self.codec = IntegerCodec(self.byte_size)

    def _validate(self, value: int) -> None:
        """Validate the integer value is within bounds."""
        if self.byte_size > 0:  # Fixed width
            min_value = (
                0
                if not self.has_sign
                else -(1 << (8 * math.floor(self.byte_size / 2) - 1))
            )
            max_value = (
                (1 << (8 * self.byte_size)) - 1
                if not self.has_sign
                else (1 << (8 * math.floor(self.byte_size / 2) - 1)) - 1
            )
            if not min_value <= value <= max_value:
                raise ValueError(
                    f"Value must be between {min_value} and {max_value}, got {value}"
                )


def decodable_int(
    byte_size: int, has_sign=False
) -> Callable[[Type[FixedInt]], Type[FixedInt]]:
    """Decorator to make a class decodable as an integer."""

    def decorator(cls: Type[FixedInt]) -> Type[FixedInt]:
        cls.byte_size = byte_size
        cls.has_sign = has_sign

        @staticmethod
        def decode_from(
            buffer: Union[bytes, bytearray, memoryview], offset: int = 0
        ) -> Tuple[Any, int]:
            value, size = IntegerCodec(byte_size).decode_from(byte_size, buffer, offset)
            return cls(value), size

        cls.decode_from = decode_from
        return cls

    return decorator


@decodable_int(1)
class U8(FixedInt):
    ...


@decodable_int(1, has_sign=True)
class I8(FixedInt):
    ...


@decodable_int(2)
class U16(FixedInt):
    ...


@decodable_int(2, has_sign=True)
class I16(FixedInt):
    ...


@decodable_int(4)
class U32(FixedInt):
    ...


@decodable_int(4, has_sign=True)
class I32(FixedInt):
    ...


@decodable_int(8)
class U64(FixedInt):
    ...


@decodable_int(8, has_sign=True)
class I64(FixedInt):
    ...


@decodable_int(16)
class U128(FixedInt):
    ...


@decodable_int(16, has_sign=True)
class I128(FixedInt):
    ...


@decodable_int(32)
class U256(FixedInt):
    ...


@decodable_int(32, has_sign=True)
class I256(FixedInt):
    ...


@decodable_int(64)
class U512(FixedInt):
    ...
