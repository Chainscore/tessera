from typing import Union, Any, Tuple
from jam.utils.codec.base import Codable
from jam.utils.codec.primitives.bools import BooleanCodec

class Boolean(Codable):
    """
    Boolean type that implements the Codable interface.
    
    Examples:
        >>> b = Boolean(True)
        >>> bool(b)
        True
        >>> b.encode()
        b'\\x01'
        >>> Boolean.decode_from(b'\\x01')
        (Boolean(True), 1)
    """
    
    def __init__(self, value: bool):
        """
        Initialize a Boolean.
        
        Args:
            value: Python bool value
            
        Raises:
            TypeError: If value is not a bool
        """
        super().__init__(codec=BooleanCodec())
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool, got {type(value)}")
        self.value = value

    def __bool__(self) -> bool:
        """Allow using in boolean context."""
        return self.value
    
    def __eq__(self, other: Any) -> bool:
        """Equal comparison."""
        if isinstance(other, Boolean):
            return self.value == other.value
        elif isinstance(other, bool):
            return self.value == other
        return False
    
    def __hash__(self) -> int:
        """Make hashable."""
        return hash(self.value)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Boolean({self.value})"
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        """
        Decode a Boolean from a buffer.
        
        Args:
            buffer: Bytes to decode from
            offset: Starting position in buffer
            
        Returns:
            Tuple of (Boolean instance, bytes read)
        """
        value, size = BooleanCodec().decode_from(buffer, offset)
        return Boolean(value), size
