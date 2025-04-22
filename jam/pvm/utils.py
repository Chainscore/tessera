import math

from jam.utils.conv_helper.bitarray import BitArrayConversion


class PvmUtilities:
    @staticmethod
    def chi(value: int, n: int):
        # Make value (of size n) an unbounded integer
        n = int(n)
        value = int(value)
        return value + (math.floor(value // 2 ** (8 * n - 1))) * (2**64 - 2 ** (8 * n))

    @staticmethod
    def to_unsigned(x, n):
        n = int(n)
        x = int(x)
        if x < 2**(8*n - 1):
            return x
        else:
            return x - 2**(8*n)
        
    @staticmethod
    def to_signed(x, n):
        n = int(n)
        x = int(x)
        return (2**(8*n) + x) % 2**(8*n)
            
    @staticmethod
    def b(value, n, reversed = False):
        return BitArrayConversion.bytes_to_bitarray(value, "msb" if not reversed else "lsb", n)
    
    @staticmethod
    def b_inv(value):
        return BitArrayConversion.bitarray_to_bytes(value, "msb" if not reversed else "lsb")