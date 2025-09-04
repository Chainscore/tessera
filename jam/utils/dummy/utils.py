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


def create_dummy_bytes12(seed: int = 0) -> Bytes[12]:
    """Create dummy 12 byte value"""
    if seed > 0:
        random.seed(seed)
    return Bytes[12](bytes([random.randint(0, 255) for _ in range(12)]))


def create_dummy_bytes4104(seed: int = 0) -> Bytes[4104]:
    """Create dummy 4104 byte value"""
    if seed > 0:
        random.seed(seed)
    return Bytes[4104](bytes([random.randint(0, 255) for _ in range(4104)]))
