"""Work package types for the JAM protocol."""
from dataclasses import dataclass


from jam.execution.utils import decode_code_hash
from jam.types.base import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.types.state.delta import Delta
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.protocol.core import ServiceId
from jam.types.work.item import WorkItem
from jam.types.work.refine_context import RefineContext
from jam.utils.codec.primitives.bytes import BytesCodec
from jam.utils.json.serde import JsonSerde


@decodable_dataclass
@dataclass
class Authorizer(Codable, JsonSerde):
    """Authorizer structure."""

    code_hash: OpaqueHash
    params: Bytes


@decodable_vector(WorkItem)
class WorkItems(Vector[WorkItem]):
    ...

@decodable_dataclass
@dataclass
class WorkPackage(Codable, JsonSerde):
    """Work package structure."""
    # j
    authorization: Bytes
    # h
    auth_code_host: ServiceId
    # u
    code_hash: OpaqueHash
    # p
    params: Bytes
    # x
    context: RefineContext
    # w
    items: WorkItems

    def m_c(self, delta: Delta) -> (bytes, bytes):
        service_data = delta[self.auth_code_host].historical_lookup(self.context.lookup_anchor_slot, self.code_hash)
        return decode_code_hash(service_data)

    @property
    def a(self) -> OpaqueHash:
        return Hash.blake2b(self.code_hash + self.params)