"""Cryptographic types for the JAM protocol."""
from typing import NewType

# Public key types
BandersnatchPublic = NewType('BandersnatchPublic', bytes)
Ed25519Public = NewType('Ed25519Public', bytes)
BlsPublic = NewType('BlsPublic', bytes)

# Signature types
BandersnatchVrfSignature = NewType('BandersnatchVrfSignature', bytes)
BandersnatchRingVrfSignature = NewType('BandersnatchRingVrfSignature', bytes)
Ed25519Signature = NewType('Ed25519Signature', bytes)

def validate_bandersnatch_public(value: bytes) -> BandersnatchPublic:
    """Validate and create a BandersnatchPublic value."""
    if len(value) != 32:
        raise ValueError(f"BandersnatchPublic must be exactly 32 bytes, got {len(value)}")
    return BandersnatchPublic(value)

def validate_ed25519_public(value: bytes) -> Ed25519Public:
    """Validate and create an Ed25519Public value."""
    if len(value) != 32:
        raise ValueError(f"Ed25519Public must be exactly 32 bytes, got {len(value)}")
    return Ed25519Public(value)

def validate_bls_public(value: bytes) -> BlsPublic:
    """Validate and create a BlsPublic value."""
    if len(value) != 144:
        raise ValueError(f"BlsPublic must be exactly 144 bytes, got {len(value)}")
    return BlsPublic(value)

def validate_bandersnatch_vrf_signature(value: bytes) -> BandersnatchVrfSignature:
    """Validate and create a BandersnatchVrfSignature value."""
    if len(value) != 96:
        raise ValueError(f"BandersnatchVrfSignature must be exactly 96 bytes, got {len(value)}")
    return BandersnatchVrfSignature(value)

def validate_bandersnatch_ring_vrf_signature(value: bytes) -> BandersnatchRingVrfSignature:
    """Validate and create a BandersnatchRingVrfSignature value."""
    if len(value) != 784:
        raise ValueError(f"BandersnatchRingVrfSignature must be exactly 784 bytes, got {len(value)}")
    return BandersnatchRingVrfSignature(value)

def validate_ed25519_signature(value: bytes) -> Ed25519Signature:
    """Validate and create an Ed25519Signature value."""
    if len(value) != 64:
        raise ValueError(f"Ed25519Signature must be exactly 64 bytes, got {len(value)}")
    return Ed25519Signature(value) 