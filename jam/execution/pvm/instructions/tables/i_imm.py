from typing import Dict

from jam.execution.pvm.instructions.opcode import OpReturn
from jam.execution.pvm.utils import chi
from jam.execution.pvm.instructions.opcode import OpCode
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import HOST
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs1Imm(InstructionTable):
    @property
    def lx(self) -> int:
        return min(4, self.skip_index)

    @property
    def vx(self) -> int:
        start = self.counter + 1
        end = start + self.lx
        return chi(
            int.from_bytes(
                self.program.zeta[start:end],
                "little"
            ),
            self.lx,
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            10: OpCode(name="ecalli", fn=cls.ecalli, gas=1, is_terminating=False),
        }

    def ecalli(
        self, registers: list, memory: Memory
    ) -> OpReturn:
        """
        OPC10: Ecalli.
        """
        return HOST(self.vx), self.counter + self.skip_index + 1, registers, memory
