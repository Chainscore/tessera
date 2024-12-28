# Public key types
from typing import NewType

from jam.types.base.byte_array import ByteArray144, ByteArray32, ByteArray96, ByteArray784, ByteArray64


BandersnatchPublic = NewType('BandersnatchPublic', ByteArray32)
Ed25519Public = NewType('Ed25519Public', ByteArray32)
BlsPublic = NewType('BlsPublic', ByteArray144)

# Signature types
BandersnatchVrfSignature = NewType('BandersnatchVrfSignature', ByteArray96)
BandersnatchRingVrfSignature = NewType('BandersnatchRingVrfSignature', ByteArray784)
Ed25519Signature = NewType('Ed25519Signature', ByteArray64)