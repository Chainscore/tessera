import math
from typing import List, Union

from jam.utils.conv_helper.bitarray import BitArrayConversion


class PvmUtilities:
    @staticmethod
    def chi(value: int, n: int) -> int:
        # Make value (of size n) an unbounded integer
        n = int(n)
        value = int(value)
        return value + (math.floor(value // 2 ** (8 * n - 1))) * (2**64 - 2 ** (8 * n))

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
    def b(value: Union[int, bytes], n, reversed = False) -> List[bool]:
        if isinstance(value, int):
            value = value.to_bytes(n)
        return BitArrayConversion.bytes_to_bitarray(value, "msb" if not reversed else "lsb", n)
    
    @staticmethod
    def b_inv(value: List[bool]) -> bytes:
        return BitArrayConversion.bitarray_to_bytes(value, "msb" if not reversed else "lsb")
    
    @staticmethod
    def compare(a: int|bool, b: int|bool, op: str) -> bool:
        return getattr(a, f"__{op}__")(b)