from jam.types import Bytes, decodable_vector, U32, Vector
from jam.types.protocol.crypto import Hash
from jam.utils.codec.primitives.integers import encode, decode

@decodable_vector(element_type=U32)
class U32Vector(Vector): ...

def fisher_yates_with_hash(array:U32Vector, l:int, random_array):
    for i in range(0, l):
        j = random_array[i] % (l - i)
        array[l - i - 1], array[j] = array[j], array[l - i - 1]


def get_random(h, l):
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

# def main():
#     array:U32Vector = U32Vector([])
#     for i in range(0, 341):
#         array.append(U32(i))
#
#     numbers = shuffle('d111a554e3e8a058ea18c05bc943fa3cad8fb1339bf9307f2f3d9228ae5c934b', array)
#     print(numbers)
#
# main()
