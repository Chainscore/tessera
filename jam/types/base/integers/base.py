from typing import Union, Any, TypeVar, cast

T = TypeVar('T', bound='BaseInteger')

class BaseInteger():
    """Base integer type"""
    
    def __init__(self, value: Union[int, 'BaseInteger']):
        """Initialize an integer."""
        if not isinstance(value, (int, BaseInteger)):
            raise TypeError(f"Expected int or BaseInteger, got {type(value)}")
        if isinstance(value, BaseInteger):
            value = value.value
        value = int(value)  
        self.value = value
    
    def __int__(self) -> int:
        """Allow conversion to int."""
        return self.value
    
    def __index__(self) -> int:
        """Allow use in slicing."""
        return self.value
    
    def __hash__(self) -> int:
        """Make hashable."""
        return hash(self.value)

    # Comparison operations
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, (BaseInteger, int)):
            return self.value == int(other)
        return NotImplemented
    
    def __lt__(self, other: Any) -> bool:
        if isinstance(other, (BaseInteger, int)):
            return self.value < int(other)
        return NotImplemented
    
    def __le__(self, other: Any) -> bool:
        if isinstance(other, (BaseInteger, int)):
            return self.value <= int(other)
        return NotImplemented
    
    def __gt__(self, other: Any) -> bool:
        if isinstance(other, (BaseInteger, int)):
            return self.value > int(other)
        return NotImplemented
    
    def __ge__(self, other: Any) -> bool:
        if isinstance(other, (BaseInteger, int)):
            return self.value >= int(other)
        return NotImplemented

    # Arithmetic operations
    def __add__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value + int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __sub__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value - int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __mul__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value * int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __truediv__(self: T, other: Any) -> float:
        if isinstance(other, (BaseInteger, int)):
            return self.value / int(other)
        return NotImplemented
    
    def __floordiv__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value // int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __mod__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value % int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __pow__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = pow(self.value, int(other))
            return cast(T, self.__class__(result))
        return NotImplemented

    # Bitwise operations
    def __and__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value & int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __or__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value | int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __xor__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value ^ int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __lshift__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value << int(other)
            return cast(T, self.__class__(result))
        return NotImplemented
    
    def __rshift__(self: T, other: Any) -> T:
        if isinstance(other, (BaseInteger, int)):
            result = self.value >> int(other)
            return cast(T, self.__class__(result))
        return NotImplemented

    # Reverse operations
    __radd__ = __add__
    __rsub__ = __sub__
    __rmul__ = __mul__
    __rtruediv__ = __truediv__
    __rfloordiv__ = __floordiv__
    __rmod__ = __mod__
    __rpow__ = __pow__
    __rand__ = __and__
    __ror__ = __or__
    __rxor__ = __xor__
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.value})"
    

