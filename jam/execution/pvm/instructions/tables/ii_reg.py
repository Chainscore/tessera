from typing import Any, Callable, Dict

from jam.execution.pvm.utils import b, z_inv, z
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.types import Accessibility
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs2Reg(InstructionTable):
    @property
    def rd(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] % 16)

    @property
    def ra(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] // 16)

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            100: OpCode(name="move_reg", fn=cls.move_reg, gas=1, is_terminating=False),
            101: OpCode(name="sbrk", fn=cls.sbrk, gas=1, is_terminating=False),
            102: OpCode(name="count_set_bits_64", fn=cls.count_set_bits(64), gas=1, is_terminating=False),
            103: OpCode(name="count_set_bits_32", fn=cls.count_set_bits(32), gas=1, is_terminating=False),
            104: OpCode(name="leading_zero_bits_64", fn=cls.leading_zero_bits(64), gas=1, is_terminating=False),
            105: OpCode(name="leading_zero_bits_32", fn=cls.leading_zero_bits(32), gas=1, is_terminating=False),
            106: OpCode(name="trailing_zero_bits_64", fn=cls.trailing_zero_bits(64), gas=1, is_terminating=False),
            107: OpCode(name="trailing_zero_bits_32", fn=cls.trailing_zero_bits(32), gas=1, is_terminating=False),
            108: OpCode(name="sign_extend_8", fn=cls.sign_extend(8), gas=1, is_terminating=False),
            109: OpCode(name="sign_extend_16", fn=cls.sign_extend(16), gas=1, is_terminating=False),
            110: OpCode(name="zero_extend_16", fn=cls.zero_extend_16, gas=1, is_terminating=False),
            111: OpCode(name="reverse_bytes", fn=cls.reverse_bytes, gas=1, is_terminating=False),
        }
    
    def move_reg(self, registers: list, memory: Memory) -> OpReturn:
        registers[self.rd] = registers[self.ra]
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def sbrk(self, registers: list, memory: Memory) -> OpReturn:
        req = registers[self.ra]  # bytes requested
        memory.alter_accessibility(memory.heap_break, req, Accessibility.WRITE)
        memory.heap_break = memory.heap_break + req

        # out of address space
        registers[self.rd] = memory.heap_break
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    @staticmethod
    def count_set_bits(bitsize: int) -> Callable[[Any, list, Memory], OpReturn]:
        def count_set_bits_impl(
                self, registers: list, memory: Memory
        ) -> OpReturn:
            registers[self.rd] = sum(
                b(
                    int(registers[self.ra]) % 2**bitsize, 
                    bitsize // 8
                )[:bitsize]
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return count_set_bits_impl
    
    @staticmethod
    def leading_zero_bits(bitsize: int) -> Callable[[Any, list, Memory], OpReturn]:
        def leading_zero_bits_impl(
                self, registers: list, memory: Memory
        ) -> OpReturn:
            try:
                leading_zeroes = b(
                        int(registers[self.ra]) % 2**bitsize, 
                        bitsize // 8
                    )[::-1].index(True)
            except ValueError:
                leading_zeroes = bitsize
            registers[self.rd] = leading_zeroes
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return leading_zero_bits_impl
    
    @staticmethod
    def trailing_zero_bits(bitsize: int) -> Callable[[Any, list, Memory], OpReturn]:
        def trailing_zero_impl(
                self, registers: list, memory: Memory
        ) -> OpReturn:
            try:
                trailing_zeroes = b(
                    registers[self.ra] % 2**bitsize,
                    bitsize // 8
                ).index(True)
            except ValueError:
                trailing_zeroes = bitsize
            registers[self.rd] = trailing_zeroes
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return trailing_zero_impl
    
    @staticmethod
    def sign_extend(bitsize: int) -> Callable[[Any, list, Memory], OpReturn]:
        def sign_extend_impl(
                self, registers: list, memory: Memory
        ) -> OpReturn:
            registers[self.rd] = z_inv(
                z(registers[self.ra] % 2**bitsize, bitsize // 8),
                8
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return sign_extend_impl
    
    def zero_extend_16(self, registers: list, memory: Memory) -> OpReturn:
        registers[self.rd] = int(registers[self.ra]) % 2**16
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def reverse_bytes(self, registers: list, memory: Memory) -> OpReturn:
        registers[self.rd] = int.from_bytes(registers[self.ra].to_bytes(8, "little")[::-1], "little")
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory