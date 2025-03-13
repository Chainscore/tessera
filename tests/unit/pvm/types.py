from dataclasses import dataclass
from jam.pvm.memory import MemoryChunk
from jam.pvm.program import Program
from jam.pvm.register import Registers
from jam.pvm.page_map import PageMap
from jam.types.base.enum import Enum
from jam.types.base.integers.fixed import U32
from jam.types.base.string import String
from jam.types.protocol.core import Gas
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.decorators import json_field, json_serializable
from jam.utils.json.serde import JsonSerde
from jam.pvm.extract import Status


@json_serializable
@decodable_dataclass
@dataclass
class Testcase(Codable):
    name: String
    initial_regs: Registers = json_field(name="initial-regs")
    initial_pc: U32 = json_field(name="initial-pc")
    initial_page_map: PageMap = json_field(name="initial-page-map")
    initial_memory: MemoryChunk = json_field(name="initial-memory")
    initial_gas: U32 = json_field(name="initial-gas")
    program: Program = json_field(name="program")
    expected_status: Status = json_field(name="expected-status")
    expected_regs: Registers = json_field(name="expected-regs")
    expected_pc: U32 = json_field(name="expected-pc")
    expected_memory: MemoryChunk = json_field(name="expected-memory")
    expected_gas: Gas = json_field(name="expected-gas")
