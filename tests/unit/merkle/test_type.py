from tsrkit_types import Bytes

from jam.types import Segment, Hash


def test_type():
    seg = Bytes.fromhex(
        "210575fdb3faeb30d578d9e89d5f96514fb731517cbaa28269f48fb1d23f4897"
    )

    h = Hash.blake2b(seg.encode())
    print("Hash", h.hex(), len(h))
