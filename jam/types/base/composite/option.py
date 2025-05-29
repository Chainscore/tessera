from typing import ClassVar, Type, Generic, TypeVar, Optional as _Opt, Union, Tuple, Any

from jam.types.base.integers import Int
from jam.utils.codec import Codable
from jam.utils.json import JsonSerde

T = TypeVar("T", bound=Codable)

class Option(Codable, JsonSerde, Generic[T]):
    """
    Option[T] wraps either no value (None) or a T.
    """
    _opt_type:  ClassVar[Type[T]]

    def __class_getitem__(cls, opt_t):
        if not isinstance(opt_t, type):
            raise TypeError("Option[...] only accepts a single type")
        name = f"Option[{opt_t.__name__}]"
        # build subclass: inherits all the Codable/JsonSerde logic
        return type(name,
                    (Option,),
                    {"_opt_type": opt_t})

    def __init__(self, value: _Opt[T] = None):
        # None is always allowed
        self._value = value
        if value:
            # enforce the chosen subtype
            if not isinstance(value, self._opt_type):
                raise TypeError(f"{value!r} is not a {self._opt_type.__name__}")
            self._value   = value

    def unwrap(self) -> T:
        return self._value

    @property
    def is_none(self):
        return self._value == None

    @property
    def is_some(self):
        return self._value != None

    # Boolean context: treat None as False
    def __bool__(self) -> bool:
        return self._value is not None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    def __eq__(self, other):
        if isinstance(other, Option):
            return other._value == self._value
        return other == self._value

    def to_json(self):
        return self._value.to_json() if self._value else None

    @classmethod
    def from_json(cls, data):
        if data is None:
            return cls(None)
        return cls(cls._opt_type.from_json(data))

    def encode_size(self) -> int:
        inner_sz = 0 if self.is_none else self._value.encode_size()
        # Since we just have 2 choices, even using Int.encode shall give 1 byte
        return 1 + inner_sz

    def encode_into(self, buf: bytearray, offset: int = 0) -> int:
        # tag: 0 = None, 1 = Some
        buf[offset:offset+Int(1).encode_size()] = Int(1).encode() if self.is_some else bytes(1)
        if self.is_some:
            return 1 + self._value.encode_into(buf, offset+1)
        return 1

    @classmethod
    def decode_from(
        cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple[Any, int]:
        tag, tag_size = Int.decode_from(buffer, offset)
        value, val_size = None, 0
        if tag:
            value, val_size = cls._opt_type.decode_from(buffer, offset+tag_size)

        return cls(value), tag_size+val_size