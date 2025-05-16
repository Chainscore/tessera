from typing import Dict, Tuple
from jam.execution.pvm.instructions.opcode import OpCode
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import HOST, ExecutionStatus
from jam.execution.pvm.utils import PvmUtilities
from jam.execution.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, ProgramCounter, Register
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs1Imm(InstructionTable):
    @property
    def lx(self) -> int:
        return min(4, self.skip_index)

    @property
    def vx(self) -> int:
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.lx,
                self.program.zeta[self.counter + 1 : self.counter + self.skip_index + 1]
            )[0],
            self.lx,
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            10: OpCode(name="ecalli", fn=cls.ecalli, gas=Gas(1), is_terminating=False),
        }

    def ecalli(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]:
        """
        OPC10: Ecalli.
        """
        return HOST(Register(self.vx)), self.counter + self.skip_index + 1, registers, memory
