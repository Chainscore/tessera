from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import (
    TypedArray,
)

# Public key types
BandersnatchPublic = Bytes[32]
Ed25519Public = Bytes[32]
BlsPublic = Bytes[144]

BandersnatchRingRoot = Bytes[144]

# Signature types
Ed25519Signature = Bytes[64]
BandersnatchVrfSignature = Bytes[96]
BandersnatchRingVrfSignature = Bytes[784]


# Hash functions
class Hash:
    """Cryptographic hash functions that produce 32-byte outputs"""

    @staticmethod
    def blake2b(data: bytes, digest_size: int = 32) -> Bytes[32]:
        """Blake2b hash function"""
        from hashlib import blake2b

        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](blake2b(data, digest_size=digest_size).digest())

    @staticmethod
    def sha256(data: bytes) -> Bytes[32]:
        """SHA256 hash function"""
        from hashlib import sha256

        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](sha256(data).digest())

    @staticmethod
    def sha512(data: bytes) -> Bytes[64]:
        """SHA512 hash function"""
        from hashlib import sha512
        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[64](sha512(data).digest())

    @staticmethod
    def sha3256(data: bytes) -> Bytes[32]:
        """SHA3_256 hash function"""
        from hashlib import sha3_256

        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](sha3_256(data).digest())

    @staticmethod
    def keccak256(data: bytes) -> Bytes[32]:
        """SHA256 hash function"""
        from Crypto.Hash import keccak

        if not isinstance(data, bytes):
            data = bytes(data)
        return Bytes[32](keccak.new(digest_bits=256).update(data).digest())


# Hash types
HeaderHash = Bytes[32]  # ByteArray32 equivalent
StateRoot = Bytes[32]  # ByteArray32 equivalent
BeefyRoot = Bytes[32]  # ByteArray32 equivalent
OpaqueHash = Bytes[32]  # ByteArray32 equivalent
Entropy = Bytes[32]  # ByteArray32 equivalent
WorkReportHash = Bytes[32]  # ByteArray32 equivalent
