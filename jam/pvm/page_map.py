from dataclasses import dataclass
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class Page(Codable): 
    address: U32
    length: U32
    is_writable: Boolean

@decodable_vector(Page)
class PageMap(Vector): ...