"""
Minimal stub of the `py_ark_vrf` library used by Jam Network.

The real library provides sophisticated ring-VRF cryptographic
operations.  For local development, documentation generation, and
static-analysis we only need a *tiny* subset so that the code imports
cleanly.  **DO NOT** use this stub for production or security-sensitive
purposes.
"""

from __future__ import annotations

from typing import List


class PublicKey:
    """Dummy public key that simply wraps raw bytes."""

    def __init__(self, data: bytes):
        self._data = data

    # The real API offers `to_bytes()` – keep the same signature.
    def to_bytes(self) -> bytes:  # noqa: D401
        return self._data

    # The codebase calls this to build a ring commitment. We'll just concat.
    @staticmethod
    def get_ring_commitment_bytes(keys: List[bytes]) -> bytes:  # noqa: D401, ANN001
        return b"".join(keys)


class SecretKey:
    """Dummy secret key that derives a *fake* public key deterministically."""

    def __init__(self, data: bytes):
        self._data = data

    def public(self) -> PublicKey:  # noqa: D401
        # In real crypto this would compute a curve multiplication; here we
        # just mirror the data back.
        return PublicKey(self._data)