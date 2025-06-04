"""Refine context types for the JAM protocol."""

from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import HeaderHash, StateRoot, BeefyRoot, OpaqueHash
from jam.types.protocol.core import TimeSlot


OpaqueHashes = TypedVector[OpaqueHash]


@structure
class RefineContext:
    """Refine context structure."""

    anchor: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    lookup_anchor: HeaderHash
    lookup_anchor_slot: TimeSlot
    prerequisites: OpaqueHashes

    @staticmethod
    def empty() -> "RefineContext":
        return RefineContext(
            anchor=HeaderHash([0]*32),
            state_root=StateRoot([0]*32),
            beefy_root=BeefyRoot([0]*32),
            lookup_anchor=HeaderHash([0]*32),
            lookup_anchor_slot=TimeSlot(0),
            prerequisites=OpaqueHashes([]),
        )
