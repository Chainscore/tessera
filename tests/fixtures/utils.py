from jam.types import ByteArray32, Bytes, ByteArray144, ByteArray128
from jam.types.base.sequences.bytes.byte_array import ByteArray


def create_dummy_bytes32() -> ByteArray:
    """Create dummy 32 byte value"""
    return ByteArray32(bytes([i % 256 for i in range(32)]))


def create_dummy_bytes144() -> ByteArray:
    """Create dummy 144 byte value"""
    return ByteArray144(bytes([i % 256 for i in range(144)]))


def create_dummy_bytes128() -> ByteArray:
    """Create dummy 128 byte value"""
    return ByteArray128(bytes([i % 256 for i in range(128)]))


def create_dummy_bytes(length: int) -> bytes:
    """Create dummy bytes of given length"""
    return bytes([i % 256 for i in range(length)])


def create_dummy_Bytes(length: int) -> Bytes:
    """Create dummy bytes of given length"""
    return Bytes([i % 256 for i in range(length)])
