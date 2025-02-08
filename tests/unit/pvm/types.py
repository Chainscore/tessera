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
from jam.utils.codec.composite.dataclasses import decodable_dataclass

class Status(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"

@decodable_dataclass
@dataclass
class Testcase(Codable):
    name: String
    initial_regs: Registers
    initial_pc: U32
    initial_page_map: PageMap
    initial_memory: MemoryChunk
    initial_gas: U32
    program: Program
    expected_status: Status
    expected_regs: Registers
    expected_pc: U32
    expected_memory: MemoryChunk
    expected_gas: Gas