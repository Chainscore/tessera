from tsrkit_types.bytes import Bytes
# from Crypto.Hash import keccak
from sha3 import keccak_256

Bytes32 = Bytes[32]
Bytes64 = Bytes[64]
Bytes96 = Bytes[96]
Bytes144 = Bytes[144]
Bytes784 = Bytes[784]

# Public key types
BandersnatchPublic = Bytes32
Ed25519Public = Bytes32
BlsPublic = Bytes144

BandersnatchRingRoot = Bytes144

# Signature types
Ed25519Signature = Bytes64
BandersnatchVrfSignature = Bytes96
BandersnatchRingVrfSignature = Bytes784

from hashlib import blake2b, sha256, sha512, sha3_256
import os

# Hash functions
class Hash:
    """Cryptographic hash functions that produce 32-byte outputs"""

    # cache for hash results to avoid recomputation
    _blake2b_cache = {}
    _cache_max_size = 1000

    @staticmethod
    def blake2b(data: bytes, digest_size: int = 32) -> Bytes32:
        """Blake2b hash function with caching"""

        if not isinstance(data, bytes):
            data = bytes(data)

        # Use cache for common case (32-byte digest)
        if digest_size == 32:
            if data in Hash._blake2b_cache:
                return Hash._blake2b_cache[data]

            result = Bytes32(blake2b(data, digest_size=digest_size).digest())

            # Simple cache eviction when full
            if len(Hash._blake2b_cache) >= Hash._cache_max_size:
                # Remove oldest 20% of entries
                items_to_remove = Hash._cache_max_size // 5
                for _ in range(items_to_remove):
                    Hash._blake2b_cache.pop(next(iter(Hash._blake2b_cache)))

            Hash._blake2b_cache[data] = result
            return result
        else:
            return Bytes32(blake2b(data, digest_size=digest_size).digest())

    @staticmethod
    def clear_cache():
        """Clear the blake2b cache to prevent memory buildup"""
        Hash._blake2b_cache.clear()

    @staticmethod
    def sha256(data: bytes) -> Bytes32:
        """SHA256 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes32(sha256(data).digest())

    @staticmethod
    def sha512(data: bytes) -> Bytes64:
        """SHA512 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes64(sha512(data).digest())

    @staticmethod
    def sha3256(data: bytes) -> Bytes32:
        """SHA3_256 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes32(sha3_256(data).digest())

    @staticmethod
    def keccak256(data: bytes) -> Bytes32:
        """Keccak-256 hash function (optimized)"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes32(keccak_256(data).digest())


# Hash types
class HeaderHash(Bytes32):
    ...


class StateRoot(Bytes32):
    ...


class BeefyRoot(Bytes32):
    ...


class OpaqueHash(Bytes32):
    ...


class Entropy(Bytes32):
    ...


class WorkReportHash(Bytes32):
    ...
