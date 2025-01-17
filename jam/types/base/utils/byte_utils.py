from typing import List, Literal, Optional, Sequence, Union

# Data that can be converted to sequence of bytes
Bytable = Union[int, bool, bytes, str, bytearray, memoryview, Sequence]

class ByteUtils:
    """Utility class for converting between different byte-related data types"""
    
    # Convert everything to bytes
    @staticmethod
    def int_to_bytes(value: int, length: int = None) -> bytes:
        """Convert integer to bytes with optional fixed length"""
        if length is None:
            length = (value.bit_length() + 7) // 8
        return value.to_bytes(length, byteorder='big')

    @staticmethod
    def bytes_to_int(value: bytes) -> int:
        """Convert bytes to integer"""
        return int.from_bytes(value, byteorder='big')

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        """Convert hex string to bytes"""
        hex_str = hex_str.replace('0x', '').replace(' ', '')
        return bytes.fromhex(hex_str)

    @staticmethod
    def bytes_to_hex(value: bytes) -> str:
        """Convert bytes to hex string"""
        return value.hex()
    
    @staticmethod
    def to_bytes(value: Bytable) -> bytearray:
        """Convert [str (hex_string), int, bool, bytes, memoryview] to bytearray"""
        if isinstance(value, str):
            byt = ByteUtils.hex_to_bytes(value)
        elif isinstance(value, int):
            """If it's an integer or bool, we can convert it to bytes"""
            byt = ByteUtils.int_to_bytes(value)
        else:
            """For any other type, we assume there is a __bytes__ method - if not throw an error"""
            try:
                byt = bytes(value)
            except Exception as e:
                """Catch any other error"""
                raise TypeError(f"468277217587568142: Failed to convert ${type(value)} to bytes. Full Error: {e}")
        return bytearray(byt)

    @staticmethod
    def bool_to_bytes(value: bool) -> bytes:
        """Convert boolean to bytes"""
        return bytes([1 if value else 0])

    @staticmethod
    def bytes_to_bool(value: bytes) -> bool:
        """Convert bytes to boolean"""
        return bool(value[0]) if value else False

    @staticmethod
    def bitarray_to_bytes(bits: List[bool], bitorder: Literal["msb", "lsb"] = "msb") -> bytes:
        """Convert bit array to bytes
        
        Args:
            bits: List of boolean values representing bits
            bitorder: If "msb" (default), treats first bit as most significant.
                    If "lsb", treats first bit as least significant.
        """
        result = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(min(8, len(bits) - i)):
                if bits[i + j]:
                    if bitorder == "msb":
                        byte |= (1 << (7 - j))  # MSB first
                    else:
                        byte |= (1 << j)        # LSB first
            result.append(byte)
        return bytes(result)

    @staticmethod
    def bytes_to_bitarray(value: bytes, bitorder: Literal["msb", "lsb"] = "msb") -> List[bool]:
        """Convert bytes to bit array
        
        Args:
            value: Bytes to convert
            bitorder: If "msb" (default), outputs bits with most significant first.
                    If "lsb", outputs bits with least significant first.
        """
        result = []
        for byte in value:
            for i in range(8):
                if bitorder == "msb":
                    result.append(bool((byte >> (7 - i)) & 1))  # MSB first
                else:
                    result.append(bool((byte >> i) & 1))        # LSB first
        return result

    @staticmethod
    def str_to_bytes(value: str, encoding: str = 'utf-8') -> bytes:
        """Convert string to bytes"""
        return value.encode(encoding)

    @staticmethod
    def bytes_to_str(value: bytes, encoding: str = 'utf-8') -> str:
        """Convert bytes to string"""
        return value.decode(encoding)

    # Higher level conversion utilities
    @classmethod
    def hex_to_bitarray(cls, hex_str: str) -> List[bool]:
        """Convert hex string to bit array"""
        return cls.bytes_to_bitarray(cls.hex_to_bytes(hex_str))

    @classmethod
    def bitarray_to_hex(cls, bits: List[bool]) -> str:
        """Convert bit array to hex string"""
        return cls.bytes_to_hex(cls.bitarray_to_bytes(bits))

    @classmethod
    def int_to_bitarray(cls, value: int, length: Optional[int] = None) -> List[bool]:
        """Convert integer to bit array"""
        return cls.bytes_to_bitarray(cls.int_to_bytes(value, length))

    @classmethod
    def bitarray_to_int(cls, bits: List[bool]) -> int:
        """Convert bit array to integer"""
        return cls.bytes_to_int(cls.bitarray_to_bytes(bits))

    @classmethod
    def hex_to_int(cls, hex_str: str) -> int:
        """Convert hex string to integer"""
        return cls.bytes_to_int(cls.hex_to_bytes(hex_str))

    @classmethod
    def int_to_hex(cls, value: int, length: Optional[int] = None) -> str:
        """Convert integer to hex string"""
        return cls.bytes_to_hex(cls.int_to_bytes(value, length))
    
    @staticmethod
    def bytable_to_bitarray(value: bytearray) -> List[bool]:
        """Convert bytearray to bitarray"""

if __name__ == "__main__":
    test_data = 300
    print(len(ByteUtils.int_to_bytes(300)))