import math
from typing import List


def chi(value: int, n: int) -> int:
    # Make value (of size n) an unbounded integer
    return value + (math.floor(value / 2 ** (8 * n - 1)) * (2**64 - 2 ** (8 * n)))


def z(x: int, n: int) -> int:
    """
    Z function
    convert unsigned integers to signed
    """
    if x < 2 ** (8 * n - 1):
        return x
    else:
        return x - 2 ** (8 * n)


def z_inv(x: int, n: int) -> int:
    """
    Z_inv function
    """
    n = int(n)
    x = int(x)
    return (2 ** (8 * n) + x) % 2 ** (8 * n)


def b(value: int, byte_size: int, is_reversed=False) -> List[int]:
    result = [((int(value) // 2**i) % 2) for i in range(8 * byte_size)]
    if is_reversed:
        result.reverse()
    return result


def b_inv(value: List[int], is_reversed=False) -> int:
    result = 0
    if is_reversed:
        value.reverse()
    for i in range(len(value)):
        result += value[i] * 2**i
    return result


def compare(a: int | bool, b: int | bool, op: str) -> bool:
    return getattr(a, f"__{op}__")(b)


def rtz(x: int) -> int:
    """Round towards zero"""
    if x < 0:
        return math.floor(x)
    return math.ceil(x)


def smod(a: int, b: int) -> int:
    if b == 0:
        return a
    return int((a / abs(a)) * (abs(a) % abs(b)))
