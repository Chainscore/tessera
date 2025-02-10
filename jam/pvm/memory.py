from dataclasses import dataclass
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.decorators import json_serializable
from jam.utils.json.serde import JsonSerde

@json_serializable
@decodable_dataclass
@dataclass
class Memory(Codable, JsonSerde): 
    address: U32
    contents: Bytes

@decodable_vector(Memory)
class MemoryChunk(Vector): ...