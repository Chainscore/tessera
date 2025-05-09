# from jam.merklization import BMRFunctions
# from jam.types.protocol.crypto import Hash
# from jam.types.base.null import Null
# from jam.types.base.sequences.bytes import ByteArray32
# from jam.types.base.sequences.bytes.byte_array import decodable_bytearray, ByteArray
# from jam.types import decodable_vector, Vector
# from jam.types.base.sequences.bytes import Bytes
# from jam.types.base.sequences.bytes.bit_array import Byte
# from jam.types.base.integers import Int
#
# @decodable_vector(Bytes)
# class BytesVector(Vector[Bytes]):
#     ...
#
# def main():
#
#     bmr_functions = BMRFunctions()
#
#     h1 = BytesVector([(Bytes(Byte("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842"))), Bytes(Byte("0x7507515a48439dc58bc318c48a120b656136699f42bfd2bd45473becba53462d"))])
#     res = bmr_functions.wb_merkle_fn(h1)
#     print(res)
#
#     res2 = bmr_functions._trace_fn(h1, Int(0))
#     print(res2)
#
#
#     # h2 = ByteArray32("0x7507515a48439dc58bc318c48a120b656136699f42bfd2bd45473becba53462d")
#     # h3 = ByteArray32("0x8223d5eaa57ccef85993b7180a593577fd38a65fb41e4bcea2933d8b202905f0")
#     # h4 = ByteArray32("0xa983417440b618f29ed0b7fa65212fce2d363cb2b2c18871a05c4f67217290b0")
#
# main()

from copy import deepcopy

from jam.merklization import BMRFunctions
from jam.types import Int, Bytes, Byte, Vector
from jam.types.base.sequences.bytes.byte_array import ByteArray, ByteArray32
from jam.types.work.segment import Segments, Segment, ByteArray4104
from jam.types.protocol.crypto import Hash, OpaqueHash


# from jam.work_package.work_package import WorkPackageProcessing


def zero_padding(value: Bytes, n: Int):
    hash_length = len(value)
    first_index = ((abs(hash_length) + n - 1) % n) + 1

    if hash_length // n != 0:
        padding_zero = n - first_index
        for i in range(padding_zero):
            print("called")
            value.append(Byte(0))
    return value

def test_padding():
    # i = ByteArray("0x8720b97ddd6acc0f6eb66e095524038675a4e4067adc10ec39939eaefc47d842")
    # i = ByteArray(b"\0x1\0x2\0x3")
    i = Bytes(123)
    n = Int(7)

    print(f"input {i}")

    # wp = WorkPackageProcessing()

    o = zero_padding(i, n)

    # eo = ByteArray("0x1111100")
    # print(f"expected {eo}")
    print(f"output {o}")


def test_mb():
    i1 = Bytes("0x461236a7eb29dcffc1dd282ce1de0e0ed691fc80e91e02276fe8f778f088a1b8")
    i2 = Bytes("0xe7cb536522c1c1b41fff8021055b774e929530941ea12c10f1213c56455f29ad")
    i3 = Bytes("0xb0a487a4adf6a0eda5d69ddd2f8b241cf44204f0ff793e993e5e553b7862a1dc")
    i4 = Bytes("0x3e5d0bea78537414bd1cfdaeb0f22d743bcaba5dbffacbabce8457f4cd78f69b")
    i5 = Bytes("0xb7f8dffa65971832ec9e19719debc04b1ccd9ad27187a4943807ca756962481b")

    v: Vector[Bytes] = Vector([i1, i2, i3, i4, i5])
    # v: Vector[Bytes] = Vector([i1, i2, i3])

    bmr = BMRFunctions()
    op = 0
    # op = bmr.wb_merkle_fn(v)
    # 0xe10b77e2d9708e38e009af1a84d20c0570d5a748fbef5f5cf197730d7996c948

    # op = bmr.cd_merkle_fn(v)
    # 0x165953484f6b286e273a2932eb2dd0221feedd2ab61ff167823bbdadddcc1199

    # op = bmr.leaf_page_fn(v, 1, 0)
    # Vector([0x8d556e635ef8f6a7f97e9cea15bea981130c41dced0ba2caa87c1ecbf26f0c81,0x7f05fbf2d279e583ab1f6889c460920ab0ff7c062b56bdf358576910826a8a8d])

    # op = bmr.leaf_page_fn(v, 1, 1)
    # Vector([0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8, 0xd49e47badc5d8785aa1745d6268874ccee04d9b1a5ebbbca7dff3a64c7c61070])

    # op = bmr.leaf_page_fn(v, 1, 2)
    # Vector([0xd70c5c1c466aa2f9e7ccaa41b194cbb5ad169e1c18d7b06f55be6664a3c40fb8])

    # op = bmr.merkle_path_fn(v, 0, 0)
    # [0x974c999813e81ed9f37fe5ca46dea122694abd5f129ee4574b4eb66d4a9feac1, 0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8]
    # [0x974c999813e81ed9f37fe5ca46dea122694abd5f129ee4574b4eb66d4a9feac1, 0x6818ecd5a12f3993471d07f8f7793cc033455bdd5378f8862e40945cef3539a8, 0x7f05fbf2d279e583ab1f6889c460920ab0ff7c062b56bdf358576910826a8a8d]

    # op = bmr._trace_fn(v, 0)
    # Vector([0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808, 0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808, 0xa3d5f48b6b23c308d80b4ff9d9f02fffd5183460848b0288d45a20b608d25808])

    print(f"op {op}")



def test_merkle():
    segments: Segments = Segments([])

    for i in range(10):
        val = f"segment {i}".encode()
        val = val.ljust(4104, b'\0')
        new_seg = Segment(ByteArray4104(val))

        segments.append(new_seg)

    segments2: Vector[ByteArray32] = Vector([])

    for i in range(1024):
        val = f"segment {i}".encode()
        val = val.ljust(32, b'\0')
        new_seg = ByteArray32(val)

        segments2.append(new_seg)

    # comp = deepcopy(segments)

    bmr = BMRFunctions()
    root = bmr.wb_merkle_fn(segments2)
    print(f"root {root}")
    # res = bmr._trace_fn(segments, Int(9))
    # print("segments 3", segments[3])
    # pages = bmr.merkle_path_fn(segments, int(0), int(5))
    trace = bmr.trace_fn(segments2, 1023)
    print("trace", trace)
    res = bmr.verify_proof2(trace, segments2[1023], 1023, root)
    # print("pages", len(pages), pages)
    print(res)

    # Vector([0x2fcd8539b990993e5aabe7f2eaff4d18f7ba934e278cc236336d82da81ada1a2,
    #         0x6967f429248f1503aa4d110bb25bd82efca265741828407f06e8259ddc30359a,
    #         0x43a79651e593dd4baf72d6f35f2e990fb0892915b574dae24686ddadbd81943b,
    #         0xdaea86416c39b672793117043d4413ecc7a091d029ee73d18f53e0ee24f34ec7,
    #         0x47dcc8f8c6e6e64f313ad89f025b1817ad23cc3fb67733a0b2707ef52814cb67,
    #         0xf879621b07eb5d78edf663543ea105d550440b5085409830fc744ba44f5b1d9f,
    #         0x5ac0987cf3b07ee324cc3a9473e4d4e8b2f8cd07b0c49be095ca412b139b0834,
    #         0x7263fb445b1ec553a65b319df2ea93b198b29733c35df5de7c07fc35c0a59991,
    #         0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099,
    #         0xe0aebdd9d98f01846e5b33a48c318840338a8aa20ad82dd0650b7f1070f93db7,
    #         0x0000000000000000000000000000000000000000000000000000000000000000,
    #         0x0000000000000000000000000000000000000000000000000000000000000000,
    #         0x0000000000000000000000000000000000000000000000000000000000000000,
    #         0x0000000000000000000000000000000000000000000000000000000000000000,
    #         0x0000000000000000000000000000000000000000000000000000000000000000,
    #         0x0000000000000000000000000000000000000000000000000000000000000000])

    # root - 0x39133a76d3e201912ecc035d91fc84d0dc9cc2f377aa569217a7eb390548767d
    #
    # Leaves -
    # Vector([0x2fcd8539b990993e5aabe7f2eaff4d18f7ba934e278cc236336d82da81ada1a2,
    #         0x6967f429248f1503aa4d110bb25bd82efca265741828407f06e8259ddc30359a,
    #         0x43a79651e593dd4baf72d6f35f2e990fb0892915b574dae24686ddadbd81943b,
    #         0xdaea86416c39b672793117043d4413ecc7a091d029ee73d18f53e0ee24f34ec7,
    #         0x47dcc8f8c6e6e64f313ad89f025b1817ad23cc3fb67733a0b2707ef52814cb67,
    #         0xf879621b07eb5d78edf663543ea105d550440b5085409830fc744ba44f5b1d9f,
    #         0x5ac0987cf3b07ee324cc3a9473e4d4e8b2f8cd07b0c49be095ca412b139b0834,
    #         0x7263fb445b1ec553a65b319df2ea93b198b29733c35df5de7c07fc35c0a59991,
    #         0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099,
    #         0xe0aebdd9d98f01846e5b33a48c318840338a8aa20ad82dd0650b7f1070f93db7])
    #
    # Path -
    # Vector([0xcdc867685e6d7e9105610b87a917ac2cc577e54c7f4953f87c58dac4e5b9a692,
    #         0xa13c308d3b81f742d856ccf5af5191b6d32fbbdb94b98d3efa482a0b649285a5,
    #         0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099])
    #
    # pages -
    #  [0xcdc867685e6d7e9105610b87a917ac2cc577e54c7f4953f87c58dac4e5b9a692,
    #   0xa13c308d3b81f742d856ccf5af5191b6d32fbbdb94b98d3efa482a0b649285a5,
    #   0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099]


    # test = Vector([Bytes(Byte('0xcdc867685e6d7e9105610b87a917ac2cc577e54c7f4953f87c58dac4e5b9a692')),
    #         Bytes(Byte('0xa13c308d3b81f742d856ccf5af5191b6d32fbbdb94b98d3efa482a0b649285a5')),
    #         Bytes(Byte('0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099'))])

    # test = ['0xcdc867685e6d7e9105610b87a917ac2cc577e54c7f4953f87c58dac4e5b9a692',
    #         '0xa13c308d3b81f742d856ccf5af5191b6d32fbbdb94b98d3efa482a0b649285a5',
    #         '0xc09c1f9292070631abbf4dfa342d2ceda446ccaade38e02e1ed1b056d4ce8099']
    #
    # LEAF_PREFIX = bytes('leaf', 'utf-8')
    # current_hash = Hash.blake2b(LEAF_PREFIX + bytes(segments[9]))

    # res1 = Hash.blake2b(test[0])
    #
    # res2 = Hash.blake2b(test[1])
    #
    # res3 = Hash.blake2b(test[2])

    # for sibling_hash in test:
    #     current_hash = Hash.blake2b(sibling_hash.encode() + current_hash.encode())

    # for i in range(0, 3):
    #     current_hash = Hash.blake2b(test[2-i].encode() + current_hash.encode())


    # print("res1", res1)
    # print("res1", res2)
    # print("res1", res3)
    # print("current_hash", current_hash)


