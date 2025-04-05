import math


class PvmUtilities:
    @staticmethod
    def chi(x, n):
        # Make n an unbounded integer
        n = int(n)
        return x + (math.floor(x // 2 ** (8 * n - 1))) * (2**64 - 2 ** (8 * n))

    @staticmethod
    def to_unsigned(x, n):
        if x < 2**(8*n - 1):
            return x
        else:
            return x - 2**(8*n)
        
    @staticmethod
    def to_signed(x, n):
        return (2**(8*n) + x) % 2**(8*n)
            
