from typing import Union, Any, Tuple
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.strings import StringCodec
from jam.utils.jstruct import JsonSerde


class String(Codable, JsonSerde):
    """
    UTF-8 encoded string type that implements the Codable interface.

    Examples:
        >>> s = String("Hello")
        >>> str(s)
        'Hello'
        >>> len(s)
        5
        >>> s.encode()
        b'\\x05Hello'  # Length prefix followed by UTF-8 bytes

    Note:
        String length is measured in UTF-16 code units, which means some Unicode
        characters (like emojis) may count as 2 units. This matches Python's
        string length behavior.
    """

    def __init__(self, value: str):
        """
        Initialize a string.

        Args:
            value: Python string value

        Raises:
            TypeError: If value is not a str
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value)}")

        super().__init__(codec=StringCodec())
        self.value = value

    def __str__(self) -> str:
        """Convert to str."""
        return self.value

    def __len__(self) -> int:
        """Get string length in UTF-16 code units."""
        return len(self.value)

    def __getitem__(self, index: Union[int, slice]) -> str:
        """Get character(s) at index or slice."""
        return self.value[index]

    def __contains__(self, item: str) -> bool:
        """Check if string contains substring."""
        return item in self.value

    def __eq__(self, other: Any) -> bool:
        """Compare for equality."""
        if isinstance(other, String):
            return self.value == other.value
        elif isinstance(other, str):
            return self.value == other
        return False

    def __hash__(self) -> int:
        """Make hashable."""
        return hash(self.value)

    def __add__(self, other: Union["String", str]) -> "String":
        """Concatenate strings."""
        if isinstance(other, String):
            return String(self.value + other.value)
        elif isinstance(other, str):
            return String(self.value + other)
        return NotImplemented

    def __repr__(self) -> str:
        """Get string representation."""
        return f'String("{self.value}")'

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple["String", int]:
        """
        Decode a String from a buffer.

        Args:
            buffer: Bytes to decode from
            offset: Starting position in buffer

        Returns:
            Tuple of (String instance, bytes read)

        Raises:
            ValueError: If buffer is too short
            UnicodeDecodeError: If buffer contains invalid UTF-8
        """
        value, size = StringCodec.decode_from(buffer, offset)
        return String(value), size
