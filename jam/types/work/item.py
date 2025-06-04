"""Work item types for the JAM protocol."""

from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId, Gas


@structure
class ImportSpec:
    """Import specification structure."""

    tree_root: OpaqueHash
    index: Uint[16]


@structure
class ExtrinsicSpec:
    """Extrinsic specification structure."""

    hash: OpaqueHash
    len: Uint[32]


ImportSpecs = TypedVector[ImportSpec]

ExtrinsicSpecs = TypedVector[ExtrinsicSpec]

@structure
class WorkItem:
    """Work item structure."""
    # s
    service: ServiceId
    # h
    code_hash: OpaqueHash
    # y
    payload: Bytes
    # g
    refine_gas_limit: Gas
    # a
    accumulate_gas_limit: Gas
    # i
    import_segments: ImportSpecs
    # x
    extrinsic: ExtrinsicSpecs
    # e
    export_count: Uint[16]
