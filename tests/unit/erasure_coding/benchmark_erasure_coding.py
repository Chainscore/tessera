import time
import pytest
from tsrkit_types import Bytes, Vector
import random
from jam.utils.erasure_coding.erasure_code import ErasureCode
from jam.models.work.manifest import Segments, Segment


def test_benchmark_erasure_coding():
    pytest.skip(
        f"For local testing"
    )
    n = 4104
    t = 256
    segment = Bytes[n * t](bytes([random.randint(0, 255) for _ in range(n * t)]))

    start = time.time()
    RS = ErasureCode()
    encodedChunks = RS.encode(segment)
    end = time.time()

    segment_size_bytes = n * t
    segment_size_mib = segment_size_bytes / (1024 * 1024)
    segment_size_mb = segment_size_bytes / 1000000

    print(f"Time taken {end - start:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB {len(encodedChunks)}")

    assert True

    # encodedChunks = encodedChunks[:343]
    # c = Vector([(bytes(encodedChunks[i]), i) for i in range(len(encodedChunks))])

    # decoded_data = RS.decode(c)
    # decoded_data = Bytes[4104](decoded_data)
    # assert segment == decoded_data

def test_benchmark_erasure_coding2():
    pytest.skip(
        f"For local testing"
    )
    n = 4104
    t = 3072
    # t=10

    segment = Segment(Bytes[n](bytes([random.randint(0, 255) for _ in range(n)])))
    encodedChunks = []
    RS = ErasureCode()

    segments = Segments([segment for _ in range(t)])

    segment_size_bytes = n * t
    segment_size_mib = segment_size_bytes / (1024 * 1024)
    segment_size_mb = segment_size_bytes / 1000000

    t1 = time.time()
    for i in range(t):
        encodedChunks = RS.encode(segment)
    e1 = time.time()
    print(f"Time taken in encoding with one segment at a time {e1 - t1:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")

    t2 = time.time()
    RS.encode_multiple_segments(segments)
    e2 = time.time()
    print(
        f"Time taken in encoding with multi_encoder {e2 - t2:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")

    encoded_chunks = encodedChunks
    print("len", len(encoded_chunks))
    c = Vector([(bytes(encoded_chunks[i]), i) for i in range(len(encoded_chunks))])
    del(c[0])
    del(c[1])
    t3 = time.time()
    decoded_data = RS.decode(c)
    e3 = time.time()
    print(f"Time taken in decoding {e3 - t3:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")

    assert True


# 1 MB = 1,000,000 bytes (10⁶)
# 1 MiB = 1,048,576 bytes (2²⁰)
