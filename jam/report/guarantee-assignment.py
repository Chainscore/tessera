from math import floor

from mesonbuild.scripts.python_info import suffix

from jam.utils.shuffle import shuffle
from jam.types import  decodable_vector, U32, Vector
from jam.state.state import State
from jam.types import Block
from jam.utils.constants import VALIDATOR_COUNT, CORE_COUNT

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

    array1: U32Vector = U32Vector([])
    for i in range(6):
        array1.append(U32(i))

    validator_shuffling = shuffle(h, array1)
    print("suffled_validator", validator_shuffling)

    # number_rotation = floor((Header.slot % E)/R)

    array2: U32Vector = U32Vector([])
    for i in range(6):
        val_core = floor((C * i) / V)
        array2.append(U32(val_core))

    numbers = shuffle(h, array2)
    print("suffle_cores", numbers)
    # final  = rotate(numbers, 1)
    return numbers

print("haa bhai", validator_index_function(h))

# mapping2 = { 0: {0, 2, 5}, 1: {1, 3, 4}}


def report_curr_roatation(pre_state: State, block :Block):

    entropy = pre_state.eta[2]

    array_validator: U32Vector = U32Vector([])
    for i in range(6):
        array_validator.append(U32(i))

    shuffle_validator = shuffle(entropy, array_validator)
    print("suffle_validator", shuffle_validator)

    array_cores: U32Vector = U32Vector([])
    for i in range(CORE_COUNT):
        val_core = floor((CORE_COUNT * i) / VALIDATOR_COUNT)
        array_cores.append(U32(val_core))

    shuffle_array = shuffle(entropy, array_cores)
    print("suffle_core", shuffle_array)

    curr_report_timeslot  = None
    for x in block.extrinsic.guarantees:
        curr_report_timeslot = x.slot

    rotation_phase = floor((curr_report_timeslot % E) / R)

    rotated_array = rotate(shuffle_array, rotation_phase)
    print("shuffled array with roration", rotated_array)

    mapping = {}

    # Iterate through the arrays with their indices
    for i in range(len(rotated_array)):
        value = rotated_array[i]  # Value from arr1
        group = shuffle_array[i]  # Group identifier from arr2 (0 or 1)

        # If the group (0 or 1) is not in the mapping,arr1 initialize it as an empty set
        if group not in mapping:
            mapping[group] = set()

        # Add the index from arr1 to the set for this group
        mapping[group].add(value)

    # Convert sets to sorted lists for consistent output (optional, for readability)
    result = {key: sorted(list(values)) for key, values in mapping.items()}

    # Print the result in the desired format
    print(result)   # {0: [1, 4, 5], 1: [0, 3, 4]}
    # print(result[0]) =>  [0, 2, 5]
    # print(result[0]) =>  [1, 3, 4]

    sequence = []
    for x in range(len(result)):
        sequence.append(x)


    mapping2 = []
    for x in block.extrinsic.guarantees:
        validator_indices = set()
        for y in x.signatures:
            validator_indices.add(y.validator_index)

        mapping2.append(validator_indices)



# array: U32Vector = U32Vector([])
# for i in range(6):
#     array.append(U32(i))
# # array_shuffling = shuffle(h, array)
# print("array after suffling wotour rotation", shuffle(h, array))
