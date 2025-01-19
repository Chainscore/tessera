from types import NoneType
from typing import Tuple, Union
from jam.utils.codec import Codable
from jam.utils.codec.primitives.nulls import NullCodec

class Nullable(Codable):
    """
    Null value implementation.
    
    A Null represents the absence of a value. It is encoded as an empty byte sequence.
    
    Examples:
        >>> null = Null()
        >>> encoded = null.encode()
        >>> assert encoded == b""
        >>> decoded, size = Null.decode_from(encoded)
        >>> assert decoded == null
        >>> assert size == 0
    """
    
    def __init__(self):
        """Initialize Null value."""
        super().__init__(codec=NullCodec())
        self.value = None

    def get(self) -> None:
        """
        Get the null value.
        
        Returns:
            None
        """
        return None

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Null"

    def __eq__(self, other: object) -> bool:
        """Compare for equality."""
        if isinstance(other, Nullable):
            return True
        return isinstance(other, NoneType)

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], 
        offset: int = 0
    ) -> Tuple['Nullable', int]:
        """
        Decode null value from buffer.
        
        Args:
            buffer: Source buffer
            offset: Starting offset
            
        Returns:
            Tuple of (decoded null value, bytes read)
        """
        _, size = NullCodec.decode_from(buffer, offset)
        return Null, size

Null = Nullable()