from math import floor
from typing import Dict
from jam.execution.pvm.utils import chi
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs2Reg2Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] % 16)

    @property
    def rb(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) // 16)

    @property
    def lx(self) -> int:
        return min(4, int(self.program.zeta[self.counter + 2]) % 8)

    @property
    def ly(self) -> int:
        return min(4, max(0, int(self.skip_index) - self.lx - 2))

    @property
    def vx(self) -> int:
        start = self.counter + 3
        end = start + self.lx
        return chi(int.from_bytes(self.program.zeta[start:end], "little"), self.lx)

    @property
    def vy(self) -> int:
        start = self.counter + 3 + self.lx
        end = start + self.ly
        return chi(int.from_bytes(self.program.zeta[start:end], "little"), self.ly)

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            180: OpCode(
                name="load_imm_jump_ind",
                fn=cls.load_imm_jump_ind,
                gas=1,
                is_terminating=True,
            ),
        }

    def load_imm_jump_ind(self, registers: list, memory: Memory) -> OpReturn:
        wb = registers[self.rb]
        registers[self.ra] = self.vx
        status, counter = self.program.djump(
            self.counter, floor(wb + self.vy) % 2**32
        )
        return status, counter, registers, memory
