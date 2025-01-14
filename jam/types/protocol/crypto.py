from jam.types.base import (
    ByteArray32, ByteArray64, ByteArray96,
    ByteArray144, ByteArray784
)

# Public key types
BandersnatchPublic = ByteArray32
Ed25519Public = ByteArray32
BlsPublic = ByteArray144

BandersnatchRingRoot = ByteArray144

# Signature types
Ed25519Signature = ByteArray64
BandersnatchVrfSignature = ByteArray96
BandersnatchRingVrfSignature = ByteArray784

# Hash types
HeaderHash = ByteArray32
StateRoot = ByteArray32
BeefyRoot = ByteArray32
OpaqueHash = ByteArray32
Entropy = ByteArray32
WorkReportHash = ByteArray32