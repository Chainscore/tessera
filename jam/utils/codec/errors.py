"""Error types for codec operations."""

from dataclasses import dataclass

class CodecError(Exception):
    """Base codec exception."""
    pass

@dataclass
class BufferError(CodecError):
    """Buffer operation error with expected vs actual size."""
    expected: int
    actual: int
    message: str = "Buffer error"

    def __str__(self) -> str:
        return f"{self.message}: expected {self.expected} bytes, got {self.actual}"

class EncodeError(BufferError):
    """Exception raised when encoding fails."""
    pass

class DecodeError(BufferError):
    """Exception raised when decoding fails."""
    pass