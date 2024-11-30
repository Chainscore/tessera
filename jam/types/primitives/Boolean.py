from jam.types.Codec import Codec

class Boolean(Codec[bool]):
    """Boolean type."""
    
    def __init__(self, value: bool):
        self.value = value

    def encode(self) -> bytes:
        if self.value:
            return bytes([0x01])
        else:
            return bytes([0x00])
