from dataclasses import dataclass
from typing import Any
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatusCode
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.base.string import String
from jam.types.protocol.core import Gas
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json.decorators import with_json_metadata
from jam.utils.json.serde import JsonSerde
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.base.boolean import Boolean

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
@decodable_dataclass
@dataclass
class MemoryData(Codable, JsonSerde):
    address: U32
    contents: Bytes


@decodable_vector(MemoryData)
class MemoryChunk(Vector):
    def to_memory(self, page_map: PageMap) -> Memory:
        memory_data = {}
        allowed_read_pages = []
        allowed_write_pages = []
        for memory_entry in self:
            for i, byte in enumerate(memory_entry.contents):
                memory_data[memory_entry.address + i] = Byte(byte)
        for page in page_map:
            if page.is_writable:
                allowed_write_pages.append(page.address // 2**12)
            # else:
            allowed_read_pages.append(page.address // 2**12)
        memory = Memory(memory_data, allowed_read_pages, allowed_write_pages)
        return memory


@with_json_metadata(
    initial_regs={"name": "initial-regs"},
    initial_pc={"name": "initial-pc"},
    initial_page_map={"name": "initial-page-map"},
    initial_memory={"name": "initial-memory"},
    initial_gas={"name": "initial-gas"},
    expected_status={"name": "expected-status"},
    expected_regs={"name": "expected-regs"},
    expected_pc={"name": "expected-pc"},
    expected_memory={"name": "expected-memory"},
    expected_gas={"name": "expected-gas"}
)
@decodable_dataclass
@dataclass
class Testcase(Codable, JsonSerde):
    name: String
    initial_regs: Registers
    initial_pc: U32
    initial_page_map: PageMap
    initial_memory: MemoryChunk
    initial_gas: Gas
    program: Bytes
    expected_status: ExecutionStatusCode
    expected_regs: Registers
    expected_pc: U32
    expected_memory: MemoryChunk
    expected_gas: Gas
