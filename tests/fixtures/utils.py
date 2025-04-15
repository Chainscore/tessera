import random

from jam.types.base.sequences.bytes.byte_array import ByteArray32

def create_dummy_bytes32(seed: int = 0) -> ByteArray32:
    """Create dummy 32 byte value"""
    random.seed(seed)
    return ByteArray32(bytes([random.randint(0, 255) for _ in range(32)]))

def create_dummy_bytes(length: int, seed: int = 0) -> bytes:
    """Create dummy bytes of given length"""
    random.seed(seed)
    return bytes([random.randint(0, 255) for _ in range(length)])

def create_dummy_int(bits: int, seed: int = 0) -> int:
    """Create dummy int of given number of bits"""
    random.seed(seed)
    return random.randint(0, 2**bits - 1)