import math
from typing import List, Union

from jam.utils.conv_helper.bitarray import BitArrayConversion


class PvmUtilities:
    @staticmethod
    def chi(value: int, n: int) -> int:
        # Make value (of size n) an unbounded integer
        n = int(n)
        value = int(value)
        return value + (value // 2 ** (8 * n - 1)) * (2**64 - 2 ** (8 * n))

    @staticmethod
    def z(x: int, n: int) -> int:
        """
        Z function 
        convert unsigned integers to signed
        """
        n = int(n)
        x = int(x)
        if x < 2**(8*n - 1):
            return x
        else:
            return x - 2**(8*n)
        
    @staticmethod
    def z_inv(x: int, n: int) -> int:
        """
        Z_inv function
        """
        n = int(n)
        x = int(x)
        return (2**(8*n) + x) % 2**(8*n)
            
    @staticmethod
    def b(value: Union[int, bytes], byte_size: int, is_reversed = False) -> List[bool]:
        if isinstance(value, int):
            value = value.to_bytes(byte_size)
        return BitArrayConversion.bytes_to_bitarray(value, "msb" if not is_reversed else "lsb", byte_size * 8)
    
    @staticmethod
    def b_inv(value: List[bool], is_reversed = False) -> bytes:
        return BitArrayConversion.bitarray_to_bytes(value, "msb" if not is_reversed else "lsb")
    
    @staticmethod
    def compare(a: int|bool, b: int|bool, op: str) -> bool:
        return getattr(a, f"__{op}__")(b)
    
    @staticmethod
    def rtz(x: int) -> int:
        """Round towards zero"""
        if x < 0:
            return math.floor(x)
        return math.ceil(x)
    
    @staticmethod
    def smod(a: int, b: int) -> int:
        if b == 0: 
            return a
        return a/abs(a) * (abs(a) % abs(b))