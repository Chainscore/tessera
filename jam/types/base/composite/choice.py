from typing import ClassVar, Type, Generic, TypeVar, Optional as _Opt, Union, Tuple, Any, TypeVarTuple, Unpack

from jam.types.base.integers import Int
from jam.utils.codec import Codable
from jam.utils.json import JsonSerde

Ts = TypeVarTuple("Ts")

class Choice(Codable, JsonSerde, Generic[*Ts]):
    """"""
    _opt_types: ClassVar[Ts]
    _value: Any

    def __class_getitem__(cls, *opt_t: Unpack[Ts]):
        if not isinstance(opt_t, Tuple):
            opt_t = opt_t,
        name = f"Choice[{'/'.join(op.__class__.__name__ for op in opt_t)}]"
        return type(name,
                    (Choice,),
                    {"_opt_types": opt_t})

    def __init__(self, value: Union[Unpack[Ts]]) -> None:
        # None is always allowed
        super().__init__()
        self._value = value
        if value is not None:
            # Enforce the chosen subtype
            if not isinstance(value, self._opt_types):
                raise TypeError(f"{value!r} is not a {self._opt_types}")
            self._value   = value

    def unwrap(self) -> Unpack[Ts]:
        return self._value

    @property
    def is_none(self):
        return not self._value

    @property
    def is_some(self):
        return not not self._value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._value!r})"

    def __eq__(self, other):
        if isinstance(other, Choice):
            return other._value == self._value
        return other == self._value

    def set(self, value: Union[Unpack[Ts]]):
        if not isinstance(value, self._opt_types):
            raise TypeError(f"{value!r} not in {self._opt_types}")
        self._value = value

    # TODO: JSON Serde
    # def to_json(self):
    #     return self._value.to_json() if self._value else None

    # @classmethod
    # def from_json(cls, data):
    #     if data is None:
    #         return cls(None)
    #     return cls(cls._opt_type.from_json(data))

    def encode_size(self) -> int:
        inner_sz = 0 if self.is_none else self._value.encode_size()
        # Since we just have 2 choices, even using Int.encode shall give 1 byte
        return Int(len(self._opt_types)).encode_size() + inner_sz

    def encode_into(self, buf: bytearray, offset: int = 0) -> int:
        # tag: 0 = None, 1 = Some
        buf[offset:offset+Int(1).encode_size()] = Int(self._opt_types.index(type(self._value))).encode()
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
            value, val_size = cls._opt_types[tag].decode_from(buffer, offset+tag_size)

        return cls(value), tag_size+val_size