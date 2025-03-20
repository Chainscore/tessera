from dataclasses import dataclass
from typing import List
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.general import Int
from jam.types.base.sequences.bytes import ByteArray32, Bytes
from jam.types.protocol.core import ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.state.components.delta import Timestamps
from jam.state.components.delta import PartialState
from jam.pvm.pvm_memory import PageMemory
from jam.pvm.register import Register
ServiceCodeHash = ByteArray32


@decodable_dataclass
@dataclass
class XContent(Codable, JsonSerde):
    s_index: ServiceId
    partial_state: PartialState
    i_index: ServiceId
    time_slot: Timestamps
    hash: ByteArray32


@decodable_dataclass
@dataclass
class BoldM(Codable, JsonSerde):
    blob: List
    memory: PageMemory
    i: Register


@decodable_dictionary(Int, BoldM)
class RefineMap(Dictionary[Int, BoldM]):
    ...


@decodable_dataclass
@dataclass
class Segment(Codable, JsonSerde):
    list: List[List]

