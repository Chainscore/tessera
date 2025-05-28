from jam.types.base import decodable_vector, U32, Vector, Bytes
from jam.types.protocol.crypto import Hash
from jam.utils.codec.primitives.integers import encode, decode

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

def fisher_yates_with_hash(array:U32Vector, l:int, random_array):
    """
    Description:
        This function takes three arguments: an array, the length of the array, and a random_array. It shuffles the given array based on the indices provided in random_array and returns the shuffled array.
    Args:
        array: The array that needs to be shuffled.
        l: The length of the array that is going to be shuffled.
        random_array : An array of the same length as the original array, generated using a given hash, which determines the shuffle order.

    Returns:
        Returns a shuffled array of integers.
    """
    for i in range(0, l):
        j = random_array[i] % (l - i)
        array[l - i - 1], array[j] = array[j], array[l - i - 1]


def get_random(h, l):
    """
    Description:
        The `get_random` function helps generate a `random_array` with the same length as the array to be shuffled. It takes a hash value, performs some operations on it, and generates a new `random_array`.
    Arg:
        h: hash value
        l: length of array(array to be shuffled)

    Return:
        A random_array that is generated using a hash value after performing certain operations on the hash value.    """
    random = []
    for i in range(l):
        new_h = h + encode(i // 8, 4)
        new_hash = Hash.blake2b(new_h)
        new_hash_slice = new_hash[((4 * i) % 32): ((4 * i) % 32) + 4]
        num = decode(bytes(Bytes(new_hash_slice)))
        random.append(num)
    return random


def shuffle(h, array: U32Vector) -> U32Vector:
    l = len(array)
    if not isinstance(h, bytes):
        h = bytes.fromhex(h)

    random = get_random(h, l)

    fisher_yates_with_hash(array, l, random)
    array.reverse()
    return array


