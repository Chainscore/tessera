from jam.utils.byte_utils import Bytable, ByteUtils

class Bit:
    """
    A bit is a single binary digit, either 0 or 1.
    """
    value: int
    
    def __init__(self, value: Bytable):
        # Convert everything down to bytes
        data = ByteUtils.bytes_to_int(ByteUtils.to_bytes(value))
        if data != 0 and data != 1:
            raise ValueError(f"Invalid Bit of value {value}")
        self.value = data
    
    def __eq__(self, other: object) -> bool:
        try:
            return self.value == other.value
        except Exception as e:
            return self.value == other
    
    def __and__(self, other: 'Bit') -> 'Bit':
        return Bit(self.value & other.value)
    
    def __repr__(self) -> str:
        return f"Bit({self.value})"
    
    def __bytes__(self) -> bytes:
        return bytes([self.value])
    
    def __str__(self) -> str:
        return str(self.value)
    
    def __bool__(self) -> bool:
        return bool(self.value)
    
    def __int__(self) -> int:
        return self.value
    
    def __index__(self) -> int:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)
    
    def __gt__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value > other.value
        return False
    
    def __lt__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value < other.value
        return False
    
    def __ge__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value >= other.value
        return False
    
    def __le__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value <= other.value
        return False
    
    def __ne__(self, other: object) -> bool:
        if isinstance(other, Bit):
            return self.value != other.value
        return False
