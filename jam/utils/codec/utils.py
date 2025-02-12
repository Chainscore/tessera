
# Common utility functions used by codec implementations
from typing import Union
from jam.utils.codec.errors import DecodeError, EncodeError


def check_buffer_size(buffer: Union[bytes, bytearray, memoryview], expected: int, offset: int = 0) -> None:
    """
    Check if a buffer has enough remaining space.
    
    Args:
        buffer: The buffer to check
        expected: The number of bytes needed
        offset: Starting position in the buffer
        
    Raises:
        EncodeError: If the buffer is too small
    """
    available = len(buffer) - offset
    if available < expected:
        raise EncodeError(expected, available, "Buffer too small")

def ensure_size(buffer: Union[bytes, bytearray, memoryview], expected: int, offset: int = 0) -> None:
    """
    Ensure a buffer has enough bytes available for reading.
    
    Args:
        buffer: The buffer to check
        expected: The number of bytes needed
        offset: Starting position in the buffer
        
    Raises:
        DecodeError: If the buffer is too small
    """
    available = len(buffer) - offset
    if available < expected:
        raise DecodeError(expected, available, "Insufficient bytes in buffer")