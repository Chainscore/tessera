from typing import Dict, Tuple

from jam.execution.pvm.instructions.opcode import OpReturn
from jam.execution.pvm.instructions.opcode import OpCode
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs1Imm1EwImm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] % 16)

    @property
    def vx(self) -> int:
        value = int.from_bytes(bytes(self.program.zeta[self.counter + 2 : self.counter + 10]), "little")
        return value

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            20: OpCode(name="load_imm_64", fn=cls.load_imm_64, gas=1, is_terminating=False)
        }

    def load_imm_64(
        self, registers: list, memory: Memory
    ) -> OpReturn:
        """
        OPC20: Load a 64-bit immediate value into a register.
        """
        _vx = self.vx
        registers[self.ra] = _vx
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory