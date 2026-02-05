import os
import time
import pytest
from tsrkit_types import Bytes

from jam.models import Hash


def keccak256(data: bytes) -> Bytes[32]:
    """Keccak-256 hash function using PyCryptodome"""
    from Crypto.Hash import keccak
    if not isinstance(data, bytes):
        data = bytes(data)
    return Bytes[32](keccak.new(digest_bits=256, data=data).digest())


# def keccakETH(data: bytes) -> Bytes[32]:
#     """Keccak-256 hash function using eth_utils"""
#     from eth_utils import keccak
#     if not isinstance(data, bytes):
#         data = bytes(data)
#     return Bytes[32](keccak(data))

def keccakPySHA3(data: bytes) -> Bytes[32]:
    """Keccak-256 hash function using pysha3"""
    import sha3
    if not isinstance(data, bytes):
        data = bytes(data)
    return Bytes[32](sha3.keccak_256(data).digest())

def keccakSHA3(data: bytes) -> Bytes[32]:
    """SHA3_256 hash function"""
    from hashlib import sha3_256

    if not isinstance(data, bytes):
        data = bytes(data)
    return Bytes[32](sha3_256(data).digest())

# Array of functions to test
HASH_FUNCS = [
    ("PyCryptodome", keccak256),
    ("pysha3", keccakPySHA3),
    # ("hashlib", keccakSHA3), # keccak implementation changed
]

def test_version_compatibility():
    HELLO_IP = b"hello"
    HELLO_OP = bytes.fromhex("1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8")
    OP = keccakPySHA3(HELLO_IP)
    OP2 = keccakSHA3(HELLO_IP)
    OP3 = keccak256(HELLO_IP)
    assert HELLO_OP == OP == OP3 != OP2

def test_hash_benchmark():
    # Generate random test inputs
    inputs = [os.urandom(i % 256 + 1) for i in range(1, 1001)]  # 1k inputs, 1–256 bytes

    # --- Correctness check ---
    mismatches = []
    for data in inputs:
        results = [(name, fn(data)) for name, fn in HASH_FUNCS]

        # Check all digests match
        digests = [digest for _, digest in results]
        if not all(d == digests[0] for d in digests):
            mismatches.append((data, results))

        # Validate digest size
        for _, digest in results:
            assert len(digest) == 32

    assert not mismatches, f"Mismatched outputs:\n{mismatches}"

    # --- Performance test ---
    timings = {}
    for name, fn in HASH_FUNCS:
        start = time.perf_counter()
        for d in inputs:
            fn(d)
        timings[name] = time.perf_counter() - start

    print("\n--- Keccak-256 Comparison ---")
    print(f"Inputs tested: {len(inputs)}")
    print(f"All outputs match: {len(mismatches) == 0}")
    for name, elapsed in timings.items():
        print(f"{name:12s} total: {elapsed:.6f} s")

    # Sanity check (fail only if absurdly slow)
    for elapsed in timings.values():
        assert elapsed < 0.5