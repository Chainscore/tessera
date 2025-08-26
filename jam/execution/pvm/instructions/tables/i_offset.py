from typing import Dict

from jam.execution.pvm.instructions.opcode import OpReturn
from jam.execution.pvm.utils import z
from jam.execution.pvm.instructions.opcode import OpCode
from jam.execution.pvm.instructions.instruction_table import InstructionTable
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE


class WArgsOneOffset(InstructionTable):
    @property
    def lx(self) -> int:
        return min(4, self.skip_index)

    @property
    def vx(self) -> int:
        start = self.counter + 1
        end = start + self.lx
        return int(self.counter) + z(
            int.from_bytes(self.program.zeta[start:end], "little"), self.lx
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            40: OpCode(name="jump", fn=cls.jump, gas=1, is_terminating=True),
        }

    def jump(self, registers: list, memory: Memory) -> OpReturn:
        status, counter = self.program.branch(self.counter, self.vx, True)
        if status == CONTINUE and counter != self.counter:
            return status, counter, registers, memory
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
