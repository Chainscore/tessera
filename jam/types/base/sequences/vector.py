from typing import Callable, Sequence, Tuple, Type, TypeVar, Union

from jam.utils.codec.codec import Codec
from .base import BaseSequence
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.vectors import VectorCodec

T = TypeVar("T", bound=Codable)


class Vector(BaseSequence[T]):
    """
    Dynamic array implementation that supports codec operations.

    The vector grows dynamically as elements are added. All standard sequence
    operations are supported. All elements must be instances of the same Codable type.
    """

    def __init__(self, initial: Sequence[T] = [], codec: Codec[T] | None = None):
        if codec is None:
            codec = VectorCodec()
        super().__init__(initial, codec=codec)


def decodable_vector(
    element_type: Type[T], max_length: int = 2**63 - 1
) -> Callable[[Type["Vector[T]"]], Type["Vector[T]"]]:
    """Decorator to make a class decodable as a vector."""

    def decorator(cls: Type["Vector[T]"]) -> Type["Vector[T]"]:
        cls._element_type = element_type

        @staticmethod
        def decode_from(
            buffer: Union[bytes, bytearray, memoryview], offset: int = 0
        ) -> Tuple["Vector[T]", int]:
            if not issubclass(element_type, Codable):
                raise TypeError("Vector element type must be Codable")

            value, size = VectorCodec.decode_from(
                element_type, buffer, offset, max_length
            )
            return cls(value), size

        cls.decode_from = decode_from
        return cls

    return decorator
