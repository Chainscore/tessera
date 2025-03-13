
from typing import List, Literal, Optional, Sequence, Union


class BitArrayConversion:
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
                        byte |= (1 << j)  # LSB first
            result.append(byte)
        return bytes(result)

    @staticmethod
    def bytes_to_bitarray(value: bytes, bitorder: Literal["msb", "lsb"] = "msb", target_length: int | None = None) -> \
    List[bool]:
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
                    result.append(bool((byte >> i) & 1))  # LSB first

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
