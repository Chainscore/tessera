from jam.types.base import (
    ByteArray32,
    ByteArray64,
    ByteArray96,
    ByteArray144,
    ByteArray784,
)
from jam.types.base.sequences.bytes.byte_array import ByteArray
from jam.types.base.sequences.bytes.bytes import Bytes

# Public key types
BandersnatchPublic = ByteArray32
Ed25519Public = ByteArray32
BlsPublic = ByteArray144

BandersnatchRingRoot = ByteArray144

# Signature types
Ed25519Signature = ByteArray64
BandersnatchVrfSignature = ByteArray96
BandersnatchRingVrfSignature = ByteArray784


# Hash functions
class Hash:
    """Cryptographic hash functions that produce 32-byte outputs"""

    @staticmethod
    def blake2b(data: bytes) -> ByteArray32:
        """Blake2b hash function"""
        from hashlib import blake2b

        if not isinstance(data, bytes):
            data = bytes(data)
        return ByteArray32(blake2b(data, digest_size=32).digest())

    @staticmethod
    def sha256(data: bytes) -> ByteArray32:
        """SHA256 hash function"""
        from hashlib import sha256

        if not isinstance(data, bytes):
            data = bytes(data)
        return ByteArray32(sha256(data).digest())


# Hash types
HeaderHash = ByteArray32
StateRoot = ByteArray32
BeefyRoot = ByteArray32
OpaqueHash = ByteArray32
Entropy = ByteArray32
WorkReportHash = ByteArray32
