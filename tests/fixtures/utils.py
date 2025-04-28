from jam.types import ByteArray32, Bytes
from jam.types.base.sequences.bytes.byte_array import ByteArray, ByteArray4104


def create_dummy_bytes32() -> ByteArray:
    """Create dummy 32 byte value"""
    return ByteArray32(bytes([i % 256 for i in range(32)]))

def create_dummy_bytes4104() -> ByteArray:
    """Create dummy 4104 byte value"""
    return ByteArray4104(bytes([i % 256 for i in range(4104)]))


def create_dummy_bytes(length: int) -> bytes:
    """Create dummy bytes of given length"""
    return bytes([i % 256 for i in range(length)])


def create_dummy_Bytes(length: int) -> Bytes:
    """Create dummy bytes of given length"""
    return Bytes([i % 256 for i in range(length)])
