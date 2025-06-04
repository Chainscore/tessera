from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.merkle import MMR
from jam.types.protocol.crypto import HeaderHash, StateRoot, OpaqueHash
from jam.utils.constants import RECENT_HISTORY_SIZE


@structure
class ReportedWorkPackage:
    """Reported work package structure."""

    hash: OpaqueHash
    exports_root: OpaqueHash


@structure
class BlockInfo:
    """Block information structure."""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    reported: TypedVector[ReportedWorkPackage]


"""Fixed-size array of block information."""
BlocksHistory = TypedArray[BlockInfo, RECENT_HISTORY_SIZE]
