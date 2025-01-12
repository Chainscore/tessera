"""Type-specific JSON encoding/decoding functions."""

from typing import Any, Type, TypeVar, Union

T = TypeVar('T')

def encode_bytes(value: Any) -> str:
    """Encode bytes-like objects to hex string."""
    if hasattr(value, 'to_bytes'):
        return f"0x{value.to_bytes().hex()}"
    if hasattr(value, 'value') and isinstance(value.value, bytes):
        return f"0x{value.value.hex()}"
    if isinstance(value, bytes):
        return f"0x{value.hex()}"
    return str(value)

def decode_bytes(data: str, target_type: Type[T]) -> T:
    """Decode hex string to bytes-like object."""
    if isinstance(data, str):
        if data.startswith("0x"):
            byte_data = bytes.fromhex(data[2:])
        else:
            byte_data = bytes.fromhex(data)
        if target_type == bytes:
            return byte_data  # type: ignore
        return target_type(byte_data)  # type: ignore
    raise TypeError(f"Expected hex string, got {type(data)}")

def encode_integer(value: Any) -> int:
    """Encode integer-like objects to JSON number."""
    if hasattr(value, 'value'):
        return int(value.value)
    return int(value)

def decode_integer(data: Any, target_type: Type[T]) -> T:
    """Decode JSON number to integer-like object."""
    if isinstance(data, str):
        try:
            data = int(data)
        except ValueError:
            raise TypeError(f"Cannot convert {data} to {target_type.__name__}")
    if not isinstance(data, (int, float)):
        raise TypeError(f"Expected number for {target_type.__name__}, got {type(data)}")
    return target_type(int(data))  # type: ignore 