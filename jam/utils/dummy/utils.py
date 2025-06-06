import random

from tsrkit_types.bytes import Bytes

def create_dummy_bytes32(seed: int = 0) -> Bytes[32]:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return Bytes[32](bytes([random.randint(0, 255) for _ in range(32)]))

def create_dummy_bytes64(seed: int = 0) -> Bytes[64]:
    """Create dummy 32 byte value"""
    if seed > 0:
        random.seed(seed)
    return Bytes[64](bytes([random.randint(0, 255) for _ in range(64)]))

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