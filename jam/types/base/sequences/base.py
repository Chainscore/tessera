from typing import Generic, TypeVar, Type, Optional, ClassVar, Union, Tuple, overload, Any

from jam.utils.codec.codable import Codable
from jam.utils.codec.composite import ArrayCodec, VectorCodec
from jam.utils.json import JsonSerde

T = TypeVar("T")

class Vector(list, Codable, JsonSerde):
    """
    Runtime‐only: provides _validate_value that can be extended,
    override append/insert/extend/__setitem__, JSON, repr, etc.
    """
    _element_type: ClassVar[Optional[Type]]
    _min_length: ClassVar[int] = 0
    _max_length: ClassVar[int] = 2**64

    def __class_getitem__(cls, params: Union[Type, int, Tuple[Type, int], Tuple[int, int], Tuple[Type, int, int]]):
        # To overwrite previous cls values
        min_l, max_l, codec, elem_t = 0, 2**64, None, None

        if isinstance(params, int) or isinstance(params, (type, TypeVar)):
            if isinstance(params, (type, TypeVar)): elem_t = params
            elif isinstance(params, int): max_l, min_l = params, params
            else: raise TypeError(f"Invalid param to define {__class__.__name__}: {params}")
        elif len(params) == 2:
            if isinstance(params[0], type) and isinstance(params[1], int): elem_t, min_l, max_l = params[0], params[1], params[1]
            elif isinstance(params[0], int) and isinstance(params[1], int): min_l, max_l = params[0], params[1]
            else: raise TypeError(f"Invalid param to define {cls.__class__.__name__}: {params}")
        elif len(params) == 3 and isinstance(params[0], (type, TypeVar)) and isinstance(params[1], int) and isinstance(params[2], int): elem_t, min_l, max_l = params
        else:
            raise TypeError(f"Invalid param to define {cls.__class__.__name__}: {params}")

        if (min_l == max_l) and max_l > 0:
            codec = ArrayCodec(max_l)
        else:
            codec = VectorCodec()

        # build a nice name
        parts = []
        if elem_t:    parts.append(elem_t.__name__)
        if min_l == max_l:
            parts.append(f"N={min_l}")
        else:
            if min_l: parts.append(f"min={min_l}")
            if max_l != 2 ** 64: parts.append(f"max={max_l}")
        name = f"{cls.__name__}[{','.join(parts)}]"
        return type(name, (cls,), {
            "_element_type": elem_t,
            "_min_length": min_l,
            "_max_length": max_l,
            "codec": codec,
        })

    def _validate(self, value):
        """For TypeChecks - added to fns that alter elements"""
        if getattr(self, "_element_type", None) is not None:
            if not isinstance(value, self._element_type):
                raise TypeError(f"{value!r} is not an instance of {self._element_type!r}")

    def _validate_self(self):
        """For Resultant Self check - added to fns that alter size"""
        if  len(self) < self._min_length:
            raise ValueError(f"Vector: Expected sequence size to be >= {self._min_length}, resultant size {len(self)}")
        elif len(self) > self._max_length:
            raise ValueError(f"Vector: Expected sequence size to be <= {self._max_length}, resultant size {len(self)}")

    def __init__(self, initial: list[T]):
        super().__init__()
        self.extend(initial)

    def append(self, v: T):
        self._validate(v)
        super().append(v)
        self._validate_self()

    def insert(self, i, v: T):
        self._validate(v)
        super().insert(i, v)
        self._validate_self()

    def extend(self, seq: list[T]):
        for val in seq:
            self._validate(val)
        super().extend(seq)
        self._validate_self()

    def __setitem__(self, i, v):
        self._validate(v)
        super().__setitem__(i, v)

    def __repr__(self):
        return f"{self.__class__.__name__}({list(self)})"


class Array(Vector): ...
class TypedArray(Vector): ...
class TypedVector(Vector): ...
class BoundedVector(Vector): ...
class TypedBoundedVector(Vector): ...