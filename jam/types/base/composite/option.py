from types import NoneType
from typing import Generic, TypeVar, Union

from jam.types.base.composite.choice import Choice, Ts

T = TypeVar("T")

class Option(Choice, Generic[T]):
    """
    Option[T] wraps either no value (None) or a T.
    """

    def __class_getitem__(cls, opt_t: T):
        if not isinstance(opt_t, type):
            raise TypeError("Option[...] only accepts a single type")
        name = f"Option[{opt_t.__class__.__name__}]"
        return type(name,
                    (Option,),
                    {"_opt_types": (NoneType, opt_t)})

    def __init__(self, val: T|None = None):
        super().__init__(val)

    def set(self, value: T):
        super().set(value)