# Public key types
from typing import NewType

from jam.types.base.byte_array import ByteArray144, ByteArray32, ByteArray96, ByteArray784, ByteArray64
from jam.types.base.integers import U32


BandersnatchPublic = ByteArray32
Ed25519Public = ByteArray32
BlsPublic = ByteArray144

# Signature types
BandersnatchVrfSignature = ByteArray96
BandersnatchRingVrfSignature = ByteArray784
Ed25519Signature = ByteArray64

HeaderHash = ByteArray32
StateRoot = ByteArray32
OpaqueHash = ByteArray32

Entropy = ByteArray32
