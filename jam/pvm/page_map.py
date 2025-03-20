from dataclasses import dataclass
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.jstruct.decorators import with_json_metadata
from jam.utils.jstruct.serde import JsonSerde


@with_json_metadata(
    is_writable={"name": "is-writable"}
)
@decodable_dataclass
@dataclass
class Page(Codable, JsonSerde):
    address: U32
    length: U32
    is_writable: Boolean


@decodable_vector(Page)
class PageMap(Vector):
    ...
