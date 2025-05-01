import random

from jam.types.base.sequences.bytes.byte_array import ByteArray32, ByteArray12
from jam.types.work.segment import ByteArray4104

from jam.types.base.sequences.bytes.byte_array import ByteArray32, ByteArray64

def create_dummy_bytes32(seed: int = 0) -> ByteArray32:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return ByteArray32(bytes([random.randint(0, 255) for _ in range(32)]))


def create_dummy_bytes12(seed: int = 0) -> ByteArray32:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return ByteArray12(bytes([random.randint(0, 255) for _ in range(12)]))


def create_dummy_bytes4104(seed: int = 0) -> ByteArray32:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return ByteArray4104(bytes([random.randint(0, 255) for _ in range(4104)]))

def create_dummy_bytes64(seed: int = 0) -> ByteArray64:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return ByteArray32(bytes([random.randint(0, 255) for _ in range(64)]))

def create_dummy_bytes(length: int, seed: int = 0) -> bytes:
    """Create dummy bytes of given length"""
    if seed > 0:
        random.seed(seed)
    return bytes([random.randint(0, 255) for _ in range(length)])

def create_dummy_int(bits: int, seed: int = 0) -> int:
    """Create dummy int of given number of bits"""
    if seed > 0:
        random.seed(seed)
    return random.randint(0, 2**bits - 1)