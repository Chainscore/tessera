from jam.types.base.utils.byte_utils import Bytable, ByteUtils

class Bit:
    """
    A bit is a single binary digit, either 0 or 1.
    """
    def __init__(self, value: Bytable):
        # Convert everything down to bytes
        data = ByteUtils.bytes_to_int(ByteUtils.to_bytes(value))
        if data != 0 and data != 1:
            raise ValueError(f"Invalid Bit of value {value}")
        self.value = data
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value == other.value
        return False
    
    def __and__(self, other: 'Bit') -> 'Bit':
        return Bit(self.value & other.value)
    
    def __repr__(self):
        return f"Bit({self.value})"
    
    def __bytes__(self):
        return bytes([self.value])
    
    def __str__(self):
        return str(self.value)
    
    def __bool__(self):
        return bool(self.value)
    
    def __int__(self) -> int:
        return self.value
    
    def __index__(self) -> int:
        return self.value