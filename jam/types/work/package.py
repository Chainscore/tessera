"""Work package types for the JAM protocol."""

from typing import Tuple, TYPE_CHECKING

from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.execution.utils import decode_code_hash
from jam.types.protocol.core import (
    ErasureRoot,
    ExportsRoot,
    ServiceId,
    WorkPackageHash,
)
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.work.item import WorkItem
from jam.types.work.execution import RefineContext
from jam.types.work.manifest import MultiSegments, MultiExtrinsics, MultiJustifications

if TYPE_CHECKING:
    from jam.types.state.delta import Delta


@structure
class WorkPackageSpec:
    """Work package specification structure."""

    # h
    hash: WorkPackageHash
    # l
    length: Uint[32]
    # u
    erasure_root: ErasureRoot
    # e
    exports_root: ExportsRoot
    # n
    exports_count: Uint[16]

    @staticmethod
    def empty():
        return WorkPackageSpec(
            hash=WorkPackageHash([0] * 32),
            length=Uint[32](0),
            erasure_root=ErasureRoot([0] * 32),
            exports_root=ExportsRoot([0] * 32),
            exports_count=Uint[16](0),
        )


@structure
class Authorizer:
    """Authorizer structure."""

    # u
    code_hash: OpaqueHash
    # p
    params: Bytes


WorkItems = TypedVector[WorkItem]


@structure
class WorkPackage:
    """Work package structure."""

    # j
    authorization: Bytes
    # h
    auth_code_host: ServiceId
    # u, p
    authorizer: Authorizer
    # x
    context: RefineContext
    # w
    items: WorkItems

    @property
    def a(self) -> OpaqueHash:
        return Hash.blake2b(
            self.authorizer.code_hash.encode() + self.authorizer.params.encode()
        )

    def m_c(self, delta: "Delta") -> Tuple[bytes, bytes]:
        service_data = delta[self.auth_code_host].historical_lookup(
            self.context.lookup_anchor_slot, self.authorizer.code_hash
        )
        return decode_code_hash(service_data)

    def hash(self) -> Bytes[32]:
        return Hash.blake2b(self.encode())


@structure
class WorkPackageBundle:
    """Work package bundle specification structure."""

    package: WorkPackage
    extrinsics: MultiExtrinsics
    import_segments: MultiSegments
    justifications: MultiJustifications
