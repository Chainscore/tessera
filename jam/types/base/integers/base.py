from typing import Any, Callable, Tuple, Type, TypeVar, Union, NewType

class BaseInteger(int):
    """Base integer type."""

    def __repr__(self):
        return f"{self.__class__.__name__}({int(self)})"

    def _wrap_op(self, other: Any, op: Callable[[int, int], int]):
        res = op(int(self), int(other))
        return type(self)(res)

    # Arithmetic
    def __add__(self, other):
        return self._wrap_op(other, int.__add__)

    def __sub__(self, other):
        return self._wrap_op(other, int.__sub__)

    def __mul__(self, other):
        return self._wrap_op(other, int.__mul__)

    def __floordiv__(self, other):
        return self._wrap_op(other, int.__floordiv__)

    def __and__(self, other):
        return self._wrap_op(other, int.__and__)

    def __or__(self, other):
        return self._wrap_op(other, int.__or__)

    def __xor__(self, other):
        return self._wrap_op(other, int.__xor__)