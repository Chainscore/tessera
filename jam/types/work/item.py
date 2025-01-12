"""Work item types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base.integers import U16, U32
from jam.types.base.bytes import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec import Codable, decodable_dataclass
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId, Gas

@decodable_dataclass
@dataclass
class ImportSpec(Codable):
    """Import specification structure."""
    tree_root: OpaqueHash
    index: U16

@decodable_dataclass
@dataclass
class ExtrinsicSpec(Codable):
    """Extrinsic specification structure."""
    hash: OpaqueHash
    len: U32

@decodable_vector(ImportSpec)
class ImportSpecs(Vector[ImportSpec]): ...

@decodable_vector(ExtrinsicSpec)
class ExtrinsicSpecs(Vector[ExtrinsicSpec]): ...

@decodable_dataclass
@dataclass
class WorkItem(Codable):
    """Work item structure."""
    service: ServiceId
    code_hash: OpaqueHash
    payload: Bytes
    refine_gas_limit: Gas
    accumulate_gas_limit: Gas
    import_segments: ImportSpecs
    extrinsic: ExtrinsicSpecs
    export_count: U16
