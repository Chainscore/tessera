from typing import (
    Dict,
    Type,
    Union,
    Optional,
    Tuple,
    TypeVar,
    Generic,
    Any,
    get_type_hints,
)
from jam.utils.codec import Codable
from jam.utils.codec.composite.choices import ChoiceCodec
from jam.utils.jstruct import JsonSerde

T = TypeVar("T")


class Choice(Codable[T], JsonSerde, Generic[T]):
    """
    A choice is a value that can be one of several possible types.

    A Choice represents a tagged union type that can hold a value of one of several
    possible Codable types. The actual type is determined by a tag byte during
    encoding/decoding.

    To use a choice, you need to define all possible types:
        >>> @decodable_choice([U8, U16])
        >>> class MyChoice(Choice): ...
        >>> my_choice: MyChoice = MyChoice(U8(1))
        >>> assert my_choice.type == U8
        >>> assert my_choice.value == U8(1)

    To use a optional choice, we'd pair it with Nullable:
        >>> @decodable_choice([U8, Nullable])
        >>> class OptionalU8(Choice): ...
        >>> my_choice: OptionalU8 = OptionalU8(U8(1))
        >>> assert my_choice.type == U8
        >>> assert my_choice.value == U8(1)
        >>> my_choice: OptionalU8 = OptionalU8(Null)
        >>> assert my_choice.type == Nullable
        >>> assert my_choice.value is None

    To use this as an enum:
        >>> @decodable_choice([String, String, String])
        >>> class OutputType(Choice): ...
    """

    # All choices
    __choices__: Dict[str, Type[Codable[T]]] = {}
    # Selected choice
    value: Dict[str, Codable[T]]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if len(cls.__choices__) != 0:
            cls.__choices__ = {}

        # Collect the annotations declared in this subclass.
        # (This will include all annotated names that are defined in the class body.)
        all_annotations = get_type_hints(cls)
        # Remove 'value', 'codec', 'type', '__choices__'
        for k, v in all_annotations.items():
            if k not in ["value", "codec", "type", "__choices__"]:
                cls.__choices__[k] = v

    def __init__(self, initial: Dict[str, Codable[T]] | Codable[T]):
        """
        Initialize Choice.

        Args:
            initial: Mapping of initial choice name and its value. Should have only one key.
        Raises:
            ValueError: If types list is empty
        """
        self.__set_internal__(initial)
        super().__init__(codec=ChoiceCodec(self.__choices__))

    def __set__(self, value: Dict[str, Codable[T]] | Codable[T]) -> None:
        self.__set_internal__(value)

    def __set_internal__(self, value: Dict[str, Codable[T]] | Codable[T]) -> None:
        """
        Set the choice value.

        Args:
            value: Value to set. Must be instance of one of the allowed types.

        Raises:
            ValueError: If value type is not in allowed types list
        """
        if not isinstance(value, dict):
            # Find first matching key with value's choice
            for key, choice_type in self.__choices__.items():
                if isinstance(value, choice_type):
                    value = {key: value}
                    break
            else:
                raise ValueError(
                    f"Value type {type(value)} is not in allowed types: {self.__choices__.keys()}"
                )

        if len(value) != 1:
            raise ValueError(f"Choice must have exactly one key, found {len(value)}")

        # Ensure the choice key+value are valid and supported
        choice_key = list(value.keys())[0]
        if choice_key not in self.__choices__.keys():
            raise ValueError(
                f"Value type {choice_key} is not in allowed types: {self.__choices__.keys()}"
            )
        choice_type = self.__choices__[choice_key]
        if not str(type(value[choice_key])) == str(choice_type):
            raise ValueError(
                f"Value type {type(value[choice_key])} is not in allowed types: {choice_type}"
            )

        # Set them
        self.value = value

    def __get__(self) -> Optional[Codable[T]]:
        """
        Get the current value.

        Returns:
            Current value or None if not set
        """
        return self.value

    def get_value(self):
        return self.value[list(self.value.keys())[0]]

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, Choice):
            return self.value == other.value
        else:
            return self.value == other

    def __bool__(self) -> bool:
        """Check if the choice has a value."""
        return self.value is not None

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.__class__.__name__}({self.value!r})"

    def get_value(self):
        return self.value[list(self.value.keys())[0]]
        
    @classmethod
    def from_json(cls, data: Any) -> "Choice[T]":
        """Create from JSON representation."""
        last_error = None
        # Go through all the choices and try to decode the data
        choice_key = list(data.keys())[0]
        if choice_key in list(cls.__choices__.keys()):
            indexOfChoice = list(cls.__choices__.keys()).index(choice_key)
            choice_type = list(cls.__choices__.values())[indexOfChoice]
            return cls({choice_key: choice_type.from_json(data[choice_key])})

        raise ValueError(
            f"No valid choice type found for {data} in {cls.__name__}: {last_error}"
        )


def decodable_choice(cls: Type[Choice]) -> Type[Choice]:
    if len(cls.__choices__) == 0:
        raise ValueError("Choice must have at least one type")

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Choice, int]:
        """
        Decode choice from buffer.

        Args:
            types: List of possible types for this choice
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
        return cls(value), size

    cls.decode_from = decode_from
    return cls
