"""Work package types for the JAM protocol."""

from typing import Tuple, TYPE_CHECKING, Union

from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from typing_extensions import TypeVar

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

T = TypeVar("T")

@structure
class WorkPackageSpec:
    """
    Set Y
    Work package specification structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/13e40213f502?v=0.7.0
    """

    # h
    hash: WorkPackageHash
    # l, bundle length
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
    # f, configuration blob
    params: Bytes


WorkItems = TypedVector[WorkItem]

@structure
class WorkPackage:
    """
    Set P
    Work package structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/1a82001a9000?v=0.7.0
    """

    # h
    auth_code_host: ServiceId
    # j
    authorization: Bytes
    # u, f
    authorizer: Authorizer
    # c
    context: RefineContext
    # w
    items: WorkItems

    @property
    def a(self) -> OpaqueHash:
        return Hash.blake2b(
            self.authorizer.code_hash + self.authorizer.params
        )

    def m_c(self, delta: "Delta") -> Tuple[bytes, bytes]:
        service_data = delta[self.auth_code_host].historical_lookup(
            self.context.lookup_anchor_slot, self.authorizer.code_hash
        )
        return decode_code_hash(service_data)

    def hash(self) -> WorkPackageHash:
        return WorkPackageHash(Hash.blake2b(self.encode()))

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset

        items = [
            self.auth_code_host,
            self.authorizer.code_hash,
            self.context,
            self.authorization,
            self.authorizer.params,
            self.items
        ]

        for item in items:
            size = item.encode_into(buffer, current_offset)
            current_offset += size

        return current_offset - offset

    @classmethod
    def decode_from(
            cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple["WorkPackage", int]:
        curr_offset = offset
        auth_code_host, size = ServiceId.decode_from(buffer, curr_offset)
        curr_offset += size
        code_hash, size = OpaqueHash.decode_from(buffer, curr_offset)
        curr_offset += size
        context, size = RefineContext.decode_from(buffer, curr_offset)
        curr_offset += size
        authorization, size = Bytes.decode_from(buffer, curr_offset)
        curr_offset += size
        params, size = Bytes.decode_from(buffer, curr_offset)
        curr_offset += size
        items, size = WorkItems.decode_from(buffer, curr_offset)
        curr_offset += size

        authorizer = Authorizer(code_hash=code_hash, params=params)

        wp = cls(
            auth_code_host=auth_code_host,
            authorization=authorization,
            authorizer=authorizer,
            context=context,
            items=items,
        )

        return wp, curr_offset - offset

@structure
class WorkPackageBundle:
    """Work package bundle specification structure."""

    package: WorkPackage
    extrinsics: MultiExtrinsics
    import_segments: MultiSegments
    justifications: MultiJustifications
