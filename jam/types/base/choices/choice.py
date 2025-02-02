from typing import Dict, Sequence, Type, Union, Optional, Tuple, TypeVar, Generic, Any, get_type_hints
from jam.utils.codec import Codable
from jam.utils.codec.composite.choices import ChoiceCodec
from jam.utils.codec.json.json_serializable import JsonSerializable

T = TypeVar('T')

class Choice(Codable[T], Generic[T]):
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

    # Selected type
    type: Type[Codable[T]]
    value: Codable[T]

    __choices__: Dict[str, Type[Codable[T]]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if len(cls.__choices__) != 0:
            cls.__choices__ = {}
        
        # Collect the annotations declared in this subclass.
        # (This will include all annotated names that are defined in the class body.)
        all_annotations = get_type_hints(cls)
        # Remove 'value', 'codec', 'type', '__choices__'
        for k, v in all_annotations.items():
            if k not in ['value', 'codec', 'type', '__choices__']:
                cls.__choices__[k] = v

    def __init__(self, initial: Codable[T]):
        """
        Initialize Choice.
        
        Args:
            types: List of possible types for this choice
            default: Optional default value
            
        Raises:
            ValueError: If types list is empty
        """
        if len(self.__choices__) == 0:
            raise ValueError("Choice must have at least one type")

        # Make sure the initial value is a valid type
        if type(initial) not in self.__choices__.values():
            raise ValueError(f"Value type {type(initial)} is not in allowed types: {self.__choices__.values()}")
        
        super().__init__(codec=ChoiceCodec(list(self.__choices__.values())))

        if not isinstance(initial, Codable):
            raise TypeError("Choice value must be Codable")
        
        self.value: Codable[T] = initial

    def __set__(self, value: Codable[T]) -> None:
        """
        Set the choice value.
        
        Args:
            value: Value to set. Must be instance of one of the allowed types.
            
        Raises:
            ValueError: If value type is not in allowed types list
        """
        if not isinstance(value, Codable):
            raise TypeError("Choice value must be Codable")
            
        if type(value) not in self.__choices__:
            raise ValueError(f"Value type {type(value)} is not in allowed types: {self.__choices__}")
            
        self.value = value

    def __get__(self) -> Optional[Codable[T]]:
        """
        Get the current value.
        
        Returns:
            Current value or None if not set
        """
        return self.value

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        try:
            return self.value == other.value
        except:  # noqa: E722
            return self.value == other
        
    def __bool__(self) -> bool:
        """Check if the choice has a value."""
        return self.value is not None

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.__class__.__name__}({self.value!r})"

    def to_json(self) -> Any:
        """Convert to JSON representation."""
        return JsonSerializable.to_json(self.value)

    @classmethod
    def from_json(cls, data: Any) -> 'Choice[T]':
        """Create from JSON representation."""
        last_error = None
        # Go through all the choices and try to decode the data
        # While checking, check if data[choices[i]] is available then try to decode it in that type
        for i, choice_type in enumerate(cls.__choices__.values()):
            if list(cls.__choices__.keys())[i] in data.keys():
                data_parsed = choice_type.from_json(data[list(cls.__choices__.keys())[i]])
                return cls(data_parsed)

        raise ValueError(f"No valid choice type found for {data} in {cls.__name__}: {last_error}")

def decodable_choice(cls: Type[Choice]) -> Type[Choice]:
    if len(cls.__choices__) == 0:
        raise ValueError("Choice must have at least one type")

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
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
        
        value, size = ChoiceCodec.decode_from(list(cls.__choices__.values()), buffer, offset)
        return cls(value), size
    
    cls.decode_from = decode_from
    return cls