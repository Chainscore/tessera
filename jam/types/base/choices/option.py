from typing import Any, Dict, Tuple, Type, Union
from jam.types.base.choices.choice import Choice
from jam.types.base.null import Null, Nullable
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.choices import ChoiceCodec


class Option(Choice):
    """
    An option is a choice that can be either None or a value.
    """

    def __init_subclass__(cls, **kwargs):
        ...

    def __init__(self, initial: Codable = Null):
        super().__init__(Option.option_to_choice(initial))

    @staticmethod
    def option_to_choice(value: Codable | Nullable) -> Dict[str, Codable]:
        if value is None or isinstance(value, Nullable):
            return {"none": Null}
        else:
            return {"some": value}

    def __set__(self, value: Codable | Nullable):
        super().__set__(Option.option_to_choice(value))

    def __get__(self) -> Codable | Nullable:
        return list(self.value.values())[0]

    @classmethod
    def from_json(cls, data: Any) -> "Option":
        """Create from JSON representation."""
        if data is None:
            return cls(Nullable())

        value = cls.__choices__["some"].from_json(data)
        return cls(value)

    def to_json(self) -> Any:
        """Convert to JSON representation."""
        if isinstance(self.value, Nullable) or self.value is None:
            return None
        return self.__get__().to_json()

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Option):
            return self.value == other.value
        return self.__get__() == other

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__get__()})"


def decodable_option(optional_type: Type[Codable]) -> Type[Option]:
    """Decodable choice"""

    def decorator(cls: Type[Option]) -> Type[Option]:
        cls.__choices__ = {"none": Nullable, "some": optional_type}

        @staticmethod
        def decode_from(
            buffer: Union[bytes, bytearray, memoryview], offset: int = 0
        ) -> Tuple[Option, int]:
            """
            Decode option from buffer.

            Args:
                optional_type: Type of the optional value
                buffer: Source buffer
                offset: Starting offset

            Returns:
                Tuple of (decoded value, bytes read)

            Raises:
                DecodeError: If buffer is invalid or too short
                ValueError: If types list is empty
            """
            if len(cls.__choices__) == 0:
                raise ValueError("Choice must have at least one type")

            value, size = ChoiceCodec.decode_from(cls.__choices__, buffer, offset)
            return cls(list(value.values())[0]), size

        cls.decode_from = decode_from
        return cls

    return decorator
