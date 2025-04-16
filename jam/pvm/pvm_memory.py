from dataclasses import dataclass
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.serde import JsonSerde
from jam.types.base.boolean import Boolean
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.string import String


@decodable_dataclass
@dataclass
class Access(Codable):
    inaccessible: Boolean
    writable: Boolean
    readable: Boolean


@decodable_dataclass
@dataclass
class Memory(Codable, JsonSerde):
    access: Access
    value: Bytes


@decodable_dictionary(U32, Memory)
class Pages(Dictionary[U32, Memory]):
    ...


@decodable_dictionary(String, Memory)
class JsonPages(Dictionary[String, Memory]):
    ...


@decodable_dataclass
@dataclass
class PageMemory(Codable):
    pages: Pages


@decodable_dataclass
@dataclass
class JsonPageMemory(Codable):
    pages: JsonPages
