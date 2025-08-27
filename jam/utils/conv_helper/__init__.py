from typing import List, Literal, Optional, Sequence, Union
import hashlib
from jam.utils.conv_helper.hex import HexConversion
from jam.utils.conv_helper.string import StrConversion

# Data that can be converted to sequence of bytes
Bytable = Union[int, bool, bytes, str, bytearray, memoryview, Sequence]


class ConversionHelper(HexConversion, StrConversion):
    @staticmethod
    def to_bytes(
        value: Bytable, byteorder: Literal["big", "little"] = "big"
    ) -> bytearray:
        """Convert [str (hex_string), int, bool, bytes, memoryview] to bytearray"""
        if isinstance(value, str):
            byt = HexConversion.hex_to_bytes(value)
        elif isinstance(value, int):
            """If it's an integer or bool, we can convert it to bytes"""
            byt = ConversionHelper.int_to_bytes(value, byteorder)
        else:
            """For any other type, we assume there is a __bytes__ method - if not throw an error"""
            try:
                byt = bytes(value)
            except Exception as e:
                """Catch any other error"""
                raise TypeError(
                    f"ByteUtils.to_bytes: Failed to convert {value} to bytes. Full Error: {e}"
                )
        return bytearray(byt)

    @staticmethod
    def to_int(value: Bytable) -> int:
        return ConversionHelper.bytes_to_int(ConversionHelper.to_bytes(value))

    @staticmethod
    def to_string(value: Bytable) -> str:
        return StrConversion.bytes_to_str(ConversionHelper.to_bytes(value))

    @staticmethod
    def to_hex(value: Bytable) -> str:
        return HexConversion.bytes_to_hex(ConversionHelper.to_bytes(value))

    @staticmethod
    def to_hash(value: bytes) -> bytes:
        return hashlib.sha512(value).digest()

    # Convert everything to bytes
    @staticmethod
    def int_to_bytes(
        value: int, length: int = None, byteorder: Literal["big", "little"] = "big"
    ) -> bytes:
        """Convert integer to bytes with optional fixed length"""
        if length is None:
            length = (value.bit_length() + 7) // 8
        print(type(value))
        return value.to_bytes(length, byteorder)

    @staticmethod
    def bytes_to_int(value: bytes, byteorder: Literal["big", "little"] = "big") -> int:
        """Convert bytes to integer"""
        return int.from_bytes(value, byteorder)
