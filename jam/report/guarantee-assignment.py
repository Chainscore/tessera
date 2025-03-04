from math import floor

from jam.utils.shuffle import shuffle
from jam.state.components.tau import Tau
from jam.state.components.eta import Eta
from jam.types import  decodable_vector, U32, Vector
from jam.types.header import Header



R = 10     #ROTATION_PERIOD_VALIDATOR_CORE_ASSIGNMENT
E = 600    #LENGTH_OF_EPOCH
C = 341    #TOTAL_CORE
V = 1023   #TOTAL_VALIDATOR

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

entropy_randomness  = "0x7b0aa1735e5ba58d3236316c671fe4f00ed366ee72417c9ed02a53a8019e85b8"
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
        val_core = floor((C*i)/V)
        array.append(U32(val_core))

    # number_rotation = floor((Header.slot % E)/R)

    numbers = shuffle(h, array)
    final  = rotate(numbers, 1)
    return final



print("haa bhai", validator_index_function(h))





# array: U32Vector = U32Vector([])
# for j in range((6)):
#     array.append(U32(j))
# numbers = shuffle(h, array)


# print(numbers)
# Ratationnumber = float((t % LENGTH_OF_EPOCH)/ROTATION_PERIOD_VALIDATOR_CORE_ASSIGNMENT)
# suffle_vaidator  = shuffle(entropy_randomness :Eta, arr)
# def permutation(shuffle, time_slot:Tau):

