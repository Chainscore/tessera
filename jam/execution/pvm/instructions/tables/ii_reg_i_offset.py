from typing import Any, Callable, Dict
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.utils import PvmUtilities
from jam.execution.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs2Reg1Offset(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def rb(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) // 16)
    
    @property
    def lx(self) -> int:
        return min(4, max(0, int(self.skip_index) - 1))
    
    @property
    def vx(self) -> int:
        start = self.counter + 2
        end = start + self.lx
        return int(self.counter) + PvmUtilities.z(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], 
            self.lx
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            170: OpCode(name="branch_eq", fn=cls.branch("eq"), gas=Gas(1), is_terminating=True),
            171: OpCode(name="branch_ne", fn=cls.branch("ne"), gas=Gas(1), is_terminating=True),
            172: OpCode(name="branch_lt_u", fn=cls.branch("lt"), gas=Gas(1), is_terminating=True),
            173: OpCode(name="branch_lt_s", fn=cls.branch("lt", True), gas=Gas(1), is_terminating=True),
            174: OpCode(name="branch_ge_u", fn=cls.branch("ge"), gas=Gas(1), is_terminating=True),
            175: OpCode(name="branch_ge_s", fn=cls.branch("ge", True), gas=Gas(1), is_terminating=True),
        }

    @staticmethod
    def branch(op: str, signed = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def branch_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            a = PvmUtilities.z(registers[self.ra], 8) if signed else registers[self.ra]
            b = PvmUtilities.z(registers[self.rb], 8) if signed else registers[self.rb]
            status, counter = self.program.branch(
                self.counter, 
                ProgramCounter(self.vx), 
                PvmUtilities.compare(a, b, op)
            )
            if status == CONTINUE and counter != self.counter:
                return status, counter, registers, memory
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return branch_impl