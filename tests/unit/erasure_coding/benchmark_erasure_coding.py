import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from tsrkit_types import Bytes, Vector
import random

from jam.utils.erasure_coding.erasure_code import ErasureCode
# from jam.utils.erasure_coding.erasure_code_2 import ErasureCode2
# from erasure_code import ErasureCoding


def test_benchmark_erasure_coding():
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
    n = 4104
    t = 3072
    # t=1
    segment = Bytes[n](bytes([random.randint(0, 255) for _ in range(n)]))
    encodedChunks = []
    RS = ErasureCode()
    # RS2 = ErasureCoding(6, 2, 4)
    # segments = [segment for _ in range(t)]

    segments = [segment for _ in range(t)]
    initialStart = time.time()

    # cProfile.run("RS.encode(segment)")
    for i in range(t):
        start = time.time()
        encodedChunks = RS.encode(segment)
        end = time.time()
        # print(f"Time taken {end-start:.3f}s")

    # with ThreadPoolExecutor() as pool:
    #     results = list(pool.map(RS.encode, segments))

    # def run(n):
    #     start = time.perf_counter()
    #     with ThreadPoolExecutor(max_workers=n) as ex:
    #         list(ex.map(RS.encode, segments))
    #     print(n, time.perf_counter() - start)
    #
    # for n in [1, 2, 4, 8]:
    #     run(n)

    totalEnd = time.time()

    segment_size_bytes = n * t
    segment_size_mib = segment_size_bytes / (1024 * 1024)
    segment_size_mb = segment_size_bytes / 1000000

    print(f"Time taken in encoding {totalEnd - initialStart:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")
    # initialStart = time.time()
    #
    # for i in range(t):
    #     start = time.time()
    #     encodedChunks = RS2.encode(segment)
    #     end = time.time()
    #     # print(f"Time taken {end - start:.3f}s")
    #
    # totalEnd = time.time()
    #
    # segment_size_bytes = n * t
    # segment_size_mib = segment_size_bytes / (1024 * 1024)
    # segment_size_mb = segment_size_bytes / 1000000
    #
    # print(
    #     f"Time taken in encoding {totalEnd - initialStart:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")

    # encoded_chunks = encodedChunks[:343]
    # t2 = time.time()
    # for _ in range(t):
    #     c = Vector([(bytes(encoded_chunks[i]), i) for i in range(len(encoded_chunks))])
    #
    #     decoded_data = RS.decode(c)
    #     # decoded_data = Bytes[4104](decoded_data)
    # e2 = time.time()
    #
    # print(f"Time taken in decoding {e2 - t2:.3f}s for {segment_size_mib:.2f} MiB segment size, {segment_size_mb:.2f}MB")
    assert True


# 1 MB = 1,000,000 bytes (10⁶)
# 1 MiB = 1,048,576 bytes (2²⁰)
