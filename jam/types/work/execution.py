"""Work execution types for the JAM protocol."""

from tsrkit_types.integers import Uint
from tsrkit_types.choice import Choice
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from tsrkit_types.null import NullType
from dataclasses import field
from jam.types.protocol.core import Gas, ServiceId, TimeSlot
from jam.types.protocol.crypto import OpaqueHash, HeaderHash, StateRoot, BeefyRoot


class WorkExecResult(Choice):
    """
    Set B U E
    Work execution result choice.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/148e00149800?v=0.7.0
    """

    ok: Bytes
    out_of_gas: NullType
    panic: NullType
    # circle dot
    bad_exports: NullType
    # circle minus
    result_oversize: NullType
    # BAD
    bad_code: NullType
    # BIG
    code_oversize: NullType


ExecResults = TypedVector[WorkExecResult]


@structure
class RefineLoad:
    """Refine load structure."""

    # u
    gas_used: Uint
    # i
    imports: Uint
    # e
    exports: Uint
    # z
    extrinsic_size: Uint
    # x
    extrinsic_count: Uint


@structure
class RefineContext:
    """
    Set C
    Refine context structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/13950213db02?v=0.7.0
    """

    # a
    anchor: HeaderHash
    # s
    state_root: StateRoot
    # b
    beefy_root: BeefyRoot
    # l
    lookup_anchor: HeaderHash
    # t
    lookup_anchor_slot: TimeSlot
    # p
    prerequisites: TypedVector[OpaqueHash]

    @staticmethod
    def empty() -> "RefineContext":
        return RefineContext(
            anchor=HeaderHash([0] * 32),
            state_root=StateRoot([0] * 32),
            beefy_root=BeefyRoot([0] * 32),
            lookup_anchor=HeaderHash([0] * 32),
            lookup_anchor_slot=TimeSlot(0),
            prerequisites=TypedVector[OpaqueHash]([]),
        )

@structure
class WorkDigest:
    """
    Set D
    Work result structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/142300147b00?v=0.7.0
    """

    # s
    service_id: ServiceId
    # c
    code_hash: OpaqueHash
    # y
    payload_hash: OpaqueHash
    # g
    accumulate_gas: Gas
    # l
    result: WorkExecResult
    # u, i, x, z, e
    refine_load: RefineLoad


WorkDigests = TypedVector[WorkDigest]  # Vector of Work Results
