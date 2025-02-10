from typing import List, Literal, Optional, Sequence, Union

# Data that can be converted to sequence of bytes
Bytable = Union[int, bool, bytes, str, bytearray, memoryview, Sequence]

class ByteUtils:
    """Utility class for converting between different byte-related data types"""
    
    # Convert everything to bytes
    @staticmethod
    def int_to_bytes(value: int, length: int = None, byteorder: Literal["big", "little"] = "big") -> bytes:
        """Convert integer to bytes with optional fixed length"""
        if length is None:
            length = (value.bit_length() + 7) // 8
        return value.to_bytes(length, byteorder)

    @staticmethod
    def bytes_to_int(value: bytes, byteorder: Literal["big", "little"] = "big") -> int:
        """Convert bytes to integer"""
        return int.from_bytes(value, byteorder)

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
                raise TypeError(f"ByteUtils.to_bytes: Failed to convert {value} to bytes. Full Error: {e}")
        return bytearray(byt)
    
    @staticmethod
    def ensure_valid_sequence(value: Sequence) -> bool:
        """Check if a sequence is valid

        Checks if all elements in the sequence are same type
        
        Args:
            value: Sequence to check
        
        Returns:
            True if the sequence is valid, False otherwise
        """
        return all(isinstance(item, type(value[0])) for item in value)
    
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
    def bytes_to_bitarray(value: bytes, bitorder: Literal["msb", "lsb"] = "msb", target_length: int|None = None) -> List[bool]:
        """Convert bytes to bit array
        
        Args:
            value: Bytes to convert
            bitorder: If "msb" (default), outputs bits with most significant first.
                    If "lsb", outputs bits with the least significant first.
        """
        result = []
        for byte in value:
            for i in range(8):
                if bitorder == "msb":
                    result.append(bool((byte >> (7 - i)) & 1))  # MSB first
                else:
                    result.append(bool((byte >> i) & 1))        # LSB first
        
        if target_length is not None:
            # If msb, remove the starting bits
            if bitorder == "msb":
                result = result[-target_length:]
                # If less than target length, pad with False
                if len(result) < target_length:
                    result = [False] * (target_length - len(result)) + result
            # If lsb, remove the ending bits
            else:
                result = result[:target_length]
                # If less than target length, pad with False
                if len(result) < target_length:
                    result = result + [False] * (target_length - len(result))
        return result
    
    @staticmethod
    def str_to_bytes(value: str, encoding: str = 'utf-8') -> bytes:
        """Convert string to bytes"""
        return value.encode(encoding)

    @staticmethod
    def bytes_to_str(value: bytes, encoding: str = 'utf-8') -> str:
        """Convert bytes to string"""
        return value.decode(encoding)

    @classmethod
    def hex_to_bitarray(cls, hex_str: str) -> List[bool]:
        """Convert hex string to bit array"""
        # First convert hex to bytes, then bytes to bitarray
        return cls.bytes_to_bitarray(cls.hex_to_bytes(hex_str))

    @classmethod
    def bitarray_to_hex(cls, bits: List[bool]) -> str:
        """Convert bit array to hex string"""
        # First convert bits to bytes, then bytes to hex
        return cls.bytes_to_hex(cls.bitarray_to_bytes(bits))

    @classmethod
    def bitarray_to_int(cls, bits: List[bool], bitorder: Literal["msb", "lsb"] = "msb") -> int:
        """Convert bit array to integer"""
        result = 0
        for bit in (bits if bitorder == "msb" else reversed(bits)):
            result = (result << 1) | int(bit)
        return result

    @classmethod
    def hex_to_int(cls, hex_str: str) -> int:
        """Convert hex string to integer"""
        return int(hex_str.replace('0x', '').replace(' ', ''), 16)

    @classmethod
    def int_to_hex(cls, value: int, length: Optional[int] = None) -> str:
        """Convert integer to hex string
        
        Args:
            value: Integer to convert
            length: Optional number of bytes to pad to
        
        Returns:
            Hex string without '0x' prefix
        """
        if length is None:
            return format(value, 'x')
        return format(value, f'0{length*2}x')

    @staticmethod
    def bytable_to_bitarray(value: bytearray) -> List[bool]:
        """Convert bytearray to bitarray"""
        return ByteUtils.bytes_to_bitarray(bytes(value))
    
    @staticmethod
    def int_to_bitarray(n: int) -> list[bool]:
        """
        Convert an integer to its binary representation as a list of booleans.
        The least significant bit is at index 0.
        
        Args:
            n: The integer to convert
            
        Returns:
            A list of booleans where True represents 1 and False represents 0
            
        Examples:
            >>> int_to_bits(5)  # 5 is 101 in binary
            [True, False, True]
            >>> int_to_bits(0)
            [False]
        """
        if n == 0:
            return [False]
        
        bits = []
        while n:
            bits.append(bool(n & 1))
            n >>= 1
        
        return bits

if __name__ == "__main__":
    test_data = [0] * 10
    print(ByteUtils.to_bytes(test_data))