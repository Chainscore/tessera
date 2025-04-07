from jam.types import ByteArray32



def create_dummy_bytes32() -> ByteArray32:
    """Create dummy 32 byte value"""
    return ByteArray32(bytes([i % 256 for i in range(32)]))


def create_dummy_bytes(length: int) -> bytes:
    """Create dummy bytes of given length"""
    return bytes([i % 256 for i in range(length)])
