import math


class PvmUtilities:
    @staticmethod
    def chi(value: int, n: int):
        # Make n an unbounded integer
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
            
