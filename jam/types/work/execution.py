"""Work execution types for the JAM protocol."""

from tsrkit_types.integers import Uint
from tsrkit_types.choice import Choice
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from tsrkit_types.null import NullType

from jam.types.protocol.core import Gas, ServiceId
from jam.types.protocol.crypto import OpaqueHash


class WorkExecResult(Choice):
    """Work execution result choice."""

    ok: Bytes
    out_of_gas: NullType
    panic: NullType
    # circle dot
    bad_exports: NullType
    # BAD
    bad_code: NullType
    # BIG
    code_oversize: NullType
    # circle minus
    result_oversize: NullType


ExecResults = TypedVector[WorkExecResult]


@structure
class RefineLoad:
    """Refine load structure."""

    gas_used: Uint
    imports: Uint
    exports: Uint
    extrinsic_count: Uint
    extrinsic_size: Uint


@structure
class WorkResult:
    """Work result structure."""
    # s
    service_id: ServiceId
    # h
    code_hash: OpaqueHash
    # y
    payload_hash: OpaqueHash
    # g
    accumulate_gas: Gas
    # d
    result: WorkExecResult
    # x
    refine_load: RefineLoad 