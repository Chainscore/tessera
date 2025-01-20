"""
Codec errors.

All sorts of errors that can occur during encoding/decoding
"""

from dataclasses import dataclass

class CodecError(Exception):
    """Base class for codec-related exceptions."""
    pass

@dataclass
class BufferError(CodecError):
    """Exception raised for buffer-related errors."""
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