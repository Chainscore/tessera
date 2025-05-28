"""Work item types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base.integers import U16, U32
from jam.types.base.bytes.bytes import Bytes
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId, Gas
from jam.utils.json.serde import JsonSerde


@decodable_dataclass
@dataclass
class ImportSpec(Codable, JsonSerde):
    """Import specification structure."""

    tree_root: OpaqueHash
    index: U16


@decodable_dataclass
@dataclass
class ExtrinsicSpec(Codable, JsonSerde):
    """Extrinsic specification structure."""

    hash: OpaqueHash
    len: U32


@decodable_vector(ImportSpec)
class ImportSpecs(Vector[ImportSpec]):
    ...


@decodable_vector(ExtrinsicSpec)
class ExtrinsicSpecs(Vector[ExtrinsicSpec]):
    ...


@decodable_dataclass
@dataclass
class WorkItem(Codable, JsonSerde):
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
    export_count: U16
