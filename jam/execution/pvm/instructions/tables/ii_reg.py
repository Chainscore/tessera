from math import ceil
from typing import Any, Callable, Dict
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, PvmError, PAGE_FAULT
from jam.execution.pvm.utils import PvmUtilities
from jam.execution.pvm.instructions.instruction_table import InstructionTable
from jam.types.base import U64
from jam.types.protocol.core import Gas, Register
from jam.utils.constants import PVM_MEMORY_PAGE_SIZE

def ceil_pages(n: int) -> int:
    return (n + PVM_MEMORY_PAGE_SIZE - 1) // PVM_MEMORY_PAGE_SIZE

FAIL_SENTINEL = 1 << 63        # 0x8000_0000_0000_0000  (spec § VM Invocations)

class InstructionsWArgs2Reg(InstructionTable):
    @property
    def rd(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def ra(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] // 16)

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            100: OpCode(name="move_reg", fn=cls.move_reg, gas=Gas(1), is_terminating=False),
            101: OpCode(name="sbrk", fn=cls.sbrk, gas=Gas(1), is_terminating=False),
            102: OpCode(name="count_set_bits_64", fn=cls.count_set_bits(64), gas=Gas(1), is_terminating=False),
            103: OpCode(name="count_set_bits_32", fn=cls.count_set_bits(32), gas=Gas(1), is_terminating=False),
            104: OpCode(name="leading_zero_bits_64", fn=cls.leading_zero_bits(64), gas=Gas(1), is_terminating=False),
            105: OpCode(name="leading_zero_bits_32", fn=cls.leading_zero_bits(32), gas=Gas(1), is_terminating=False),
            106: OpCode(name="trailing_zero_bits_64", fn=cls.trailing_zero_bits(64), gas=Gas(1), is_terminating=False),
            107: OpCode(name="trailing_zero_bits_32", fn=cls.trailing_zero_bits(32), gas=Gas(1), is_terminating=False),
            108: OpCode(name="sign_extend_8", fn=cls.sign_extend(8), gas=Gas(1), is_terminating=False),
            109: OpCode(name="sign_extend_16", fn=cls.sign_extend(16), gas=Gas(1), is_terminating=False),
            110: OpCode(name="zero_extend_16", fn=cls.zero_extend_16, gas=Gas(1), is_terminating=False),
            111: OpCode(name="reverse_bytes", fn=cls.reverse_bytes, gas=Gas(1), is_terminating=False),
        }
    
    def move_reg(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = registers[self.ra]
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def sbrk(self, registers: Registers, memory: Memory) -> OpReturn:
        req = int(registers[self.ra])  # bytes requested
        if req == 0:  # ─── QUERY ONLY ───
            registers[self.rd] = Register(memory.heap_break)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory

        pages_needed = ceil_pages(req)
        region_size = pages_needed * PVM_MEMORY_PAGE_SIZE
        limit = 2 ** 32

        cursor = ((memory.heap_break + PVM_MEMORY_PAGE_SIZE - 1)
                  // PVM_MEMORY_PAGE_SIZE) * PVM_MEMORY_PAGE_SIZE

        while cursor + region_size <= limit:
            cand_pages = memory.get_pages(cursor, cursor + region_size)

            if all(p not in memory.allowed_read_pages
                   and p not in memory.allowed_write_pages for p in cand_pages):
                memory.allowed_read_pages.extend(cand_pages)  # R + W
                memory.allowed_write_pages.extend(cand_pages)
                memory.heap_break = cursor + region_size

                registers[self.rd] = Register(cursor)  # <- Register!
                return CONTINUE, self.counter + self.skip_index + 1, registers, memory

            # skip over the run of mapped pages
            cursor_page = cursor // PVM_MEMORY_PAGE_SIZE
            while (cursor_page in memory.allowed_read_pages
                   or cursor_page in memory.allowed_write_pages):
                cursor_page += 1
            cursor = cursor_page * PVM_MEMORY_PAGE_SIZE

        # out of address space
        registers[self.rd] = Register(FAIL_SENTINEL)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    @staticmethod
    def count_set_bits(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def count_set_bits_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            registers[self.rd] = Register(sum(
                PvmUtilities.b(
                    int(registers[self.ra]) % 2**bitsize, 
                    bitsize // 8
                )[:bitsize]
            ))
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return count_set_bits_impl
    
    @staticmethod
    def leading_zero_bits(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def leading_zero_bits_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            try:
                leading_zeroes = PvmUtilities.b(
                        int(registers[self.ra]) % 2**bitsize, 
                        bitsize // 8
                    )[::-1].index(True)
            except ValueError:
                leading_zeroes = bitsize
            registers[self.rd] = Register(leading_zeroes)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return leading_zero_bits_impl
    
    @staticmethod
    def trailing_zero_bits(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def trailing_zero_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            try:
                trailing_zeroes = PvmUtilities.b(
                    int(registers[self.ra]) % 2**bitsize, 
                    bitsize // 8
                ).index(True)
            except ValueError:
                trailing_zeroes = bitsize
            registers[self.rd] = Register(trailing_zeroes)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return trailing_zero_impl
    
    @staticmethod
    def sign_extend(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def sign_extend_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            registers[self.rd] = Register(PvmUtilities.z_inv(
                PvmUtilities.z(
                    int(registers[self.ra]) % 2**bitsize, 
                    bitsize // 8
                ),
                8
            ))
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return sign_extend_impl
    
    def zero_extend_16(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(int(registers[self.ra]) % 2**16)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def reverse_bytes(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register.decode_from(registers[self.ra].encode()[::-1])[0]
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory