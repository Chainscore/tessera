from types import NoneType
from jam.types.base.composite.choice import Choice


class Option(Choice):
    """
    Option[T] wraps either no value (None) or a T.
    """

    def __class_getitem__(cls, opt_t):
        if not isinstance(opt_t, type):
            raise TypeError("Option[...] only accepts a single type")
        name = f"Option[{opt_t.__name__}]"
        return type(name,
                    (Option,),
                    {"_opt_types": (NoneType, opt_t)})
