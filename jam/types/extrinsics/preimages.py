"""Preimage-related extrinsic types for the JAM protocol."""
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.core import ServiceId


@structure
class Preimage:
    """Preimage structure."""

    requester: ServiceId
    blob: Bytes


PreimagesExtrinsic = TypedVector[Preimage]