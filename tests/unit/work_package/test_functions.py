from copy import deepcopy

from jam.merklization import BMRFunctions
from jam.types import Int, Bytes, Byte, Vector
from jam.types.base.sequences.bytes.byte_array import ByteArray
from jam.types.work.segment import Segments, Segment, ByteArray4104


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

    # comp = deepcopy(segments)

    bmr = BMRFunctions()
    # root = bmr.cd_merkle_fn(segments)
    # print(f"root {root}")
    pages = bmr.merkle_path_fn(segments, Int(0), 9)
    print("pages", len(pages), pages)

