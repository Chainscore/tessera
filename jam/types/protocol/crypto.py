from tsrkit_types.bytes import Bytes
from sha3 import keccak_256

# Public key types
BandersnatchPublic = Bytes[32]
Ed25519Public = Bytes[32]
BlsPublic = Bytes[144]

BandersnatchRingRoot = Bytes[144]

# Signature types
Ed25519Signature = Bytes[64]
BandersnatchVrfSignature = Bytes[96]
BandersnatchRingVrfSignature = Bytes[784]

from hashlib import blake2b, sha256, sha512, sha3_256
import os

# Hash functions
class Hash:
    """Cryptographic hash functions that produce 32-byte outputs"""

    # cache for hash results to avoid recomputation
    _blake2b_cache = {}
    _cache_max_size = 1000

    @staticmethod
    def blake2b(data: bytes, digest_size: int = 32) -> Bytes[32]:
        """Blake2b hash function with caching"""

        if not isinstance(data, bytes):
            data = bytes(data)

        # Use cache for common case (32-byte digest)
        if digest_size == 32:
            if data in Hash._blake2b_cache:
                return Hash._blake2b_cache[data]

            result = Bytes[32](blake2b(data, digest_size=digest_size).digest())

            # Simple cache eviction when full
            if len(Hash._blake2b_cache) >= Hash._cache_max_size:
                # Remove oldest 20% of entries
                items_to_remove = Hash._cache_max_size // 5
                for _ in range(items_to_remove):
                    Hash._blake2b_cache.pop(next(iter(Hash._blake2b_cache)))

            Hash._blake2b_cache[data] = result
            return result
        else:
            return Bytes[32](blake2b(data, digest_size=digest_size).digest())

    @staticmethod
    def clear_cache():
        """Clear the blake2b cache to prevent memory buildup"""
        Hash._blake2b_cache.clear()

    @staticmethod
    def sha256(data: bytes) -> Bytes[32]:
        """SHA256 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](sha256(data).digest())

    @staticmethod
    def sha512(data: bytes) -> Bytes[64]:
        """SHA512 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[64](sha512(data).digest())

    @staticmethod
    def sha3256(data: bytes) -> Bytes[32]:
        """SHA3_256 hash function"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](sha3_256(data).digest())

    @staticmethod
    def keccak256(data: bytes) -> Bytes[32]:
        """Keccak-256 hash function (optimized)"""
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](keccak_256(data).digest())


# Hash types
class HeaderHash(Bytes[32]):
    ...


class StateRoot(Bytes[32]):
    ...


class BeefyRoot(Bytes[32]):
    ...


class OpaqueHash(Bytes[32]):
    ...


class Entropy(Bytes[32]):
    ...


class WorkReportHash(Bytes[32]):
    ...
