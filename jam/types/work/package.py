"""Work package types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId
from jam.types.work.item import WorkItem
from jam.types.work.refine_context import RefineContext

@decodable_dataclass
@dataclass
class Authorizer(Codable):
    """Authorizer structure."""
    code_hash: OpaqueHash
    params: Bytes

@decodable_vector(WorkItem)
class WorkItems(Vector[WorkItem]): ...

@decodable_dataclass
@dataclass
class WorkPackage(Codable):
    """Work package structure."""
    authorization: Bytes
    auth_code_host: ServiceId
    authorizer: Authorizer
    context: RefineContext
    items: WorkItems