from tsrkit_types import Bytes, Vector

from jam.erasure_coding.erasure_code import ErasureCode
from jam.types.work.manifest import Segments, Segment
from jam.utils.dummy.utils import create_dummy_bytes4104


def test_erasure_coding():
    RS = ErasureCode()
    segment: Segment = Segment(create_dummy_bytes4104())
    encodedChunks = RS.encode(segment)
    encodedChunks = encodedChunks[:343]
    c = Vector([(bytes(encodedChunks[i]), i) for i in range(len(encodedChunks))])

    decoded_data = RS.decode(c)
    decoded_data = Bytes[4104](decoded_data)
    assert segment == decoded_data
