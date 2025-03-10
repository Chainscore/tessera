from math import floor

from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from jam.types.header import Header

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

entropy_randomness  = "0x8c039ff7caa17ccebfcadc44bd9fce6a4b6699c4d03de2e3349aa1dc11193cd7"
h = bytes.fromhex(entropy_randomness[2:])

def rotate(nums : list[int], k: int) :
    n = len(nums)
    k %= n

    if k == 0:
        return

    i = 0
    j = (i + k) % n
    prev = nums[i]

    for _ in range(n):
        nums[j], prev = prev, nums[j]

        if j == i:
            i += 1
            j = (i + k) % n
            prev = nums[i]
            continue

        j = (j + k) % n

    return nums

def validator_index_function(h):
    array: U32Vector = U32Vector([])
    for i in range(6):
        val_core = floor((2*i)/6)
        array.append(U32(val_core))

    # number_rotation = floor((Header.slot % E)/R)

    numbers = shuffle(h, array)
    # final  = rotate(numbers, 1)
    return numbers



print("haa bhai", validator_index_function(h))

