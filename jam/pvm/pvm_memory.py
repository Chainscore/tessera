from dataclasses import dataclass
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde
from jam.types.base.boolean import Boolean
from jam.types.base.dictionary import Dictionary


@decodable_dataclass
@dataclass
class Access(Codable):
    inaccessible: Boolean
    mutable: Boolean
    immutable: Boolean


@decodable_dataclass
@dataclass
class Memory(Codable, JsonSerde):
    access: Access
    value: Bytes


@decodable_vector(Memory)
class MemoryChunk(Dictionary):
    ...
