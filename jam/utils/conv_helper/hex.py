from typing import List

Bit = bool


class HexConversion:

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        """Convert hex string to bytes"""
        hex_str = hex_str.replace("0x", "").replace(" ", "")
        return bytes.fromhex(hex_str)

    @staticmethod
    def bytes_to_hex(value: bytes) -> str:
        """Convert bytes to hex string"""
        return value.hex()
