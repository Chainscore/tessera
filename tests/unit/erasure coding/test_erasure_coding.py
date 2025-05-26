from jam.erasure_coding.erasure_code import ErasureCode
from jam.types.work.manifest import Segments, Segment, ByteArray4104
from tests.dummy.utils import create_dummy_bytes4104


def test_erasure_coding():
    RS = ErasureCode()
    segment: Segment = Segment(create_dummy_bytes4104())
    encodedChunks = RS.encode(segment)
    encodedChunks = encodedChunks[:343]
    c = [(bytes.fromhex(str(encodedChunks[i])), i) for i in range(len(encodedChunks))]

    decoded_data = RS.decode(c)
    decoded_data = ByteArray4104(decoded_data)
    assert segment == decoded_data