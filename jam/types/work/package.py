"""Work package types for the JAM protocol."""

from typing import Tuple
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.execution.utils import decode_code_hash
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.protocol.core import ServiceId
from jam.types.state.delta import Delta
from jam.types.work.item import WorkItem
from jam.types.work.refine_context import RefineContext


@structure
class Authorizer:
    """Authorizer structure."""
    # u
    code_hash: OpaqueHash
    # p
    params: Bytes

    def __hash__(self) -> int:
        return Hash.blake2b(bytes(self.code_hash) + bytes(self.params))


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

    def m_c(self, delta: Delta) -> Tuple[bytes, bytes]:
        service_data = delta[self.auth_code_host].historical_lookup(self.context.lookup_anchor_slot, self.authorizer.code_hash)
        return decode_code_hash(service_data)