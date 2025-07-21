from typing import Any, Callable, Dict

from jam.execution.pvm.utils import chi
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs1Reg2Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] % 16)

    @property
    def lx(self) -> int:
        return min(4, (self.program.zeta[self.counter + 1] // 16) % 8)

    @property
    def ly(self) -> int:
        return min(4, max(0, self.skip_index - self.lx - 1))

    @property
    def vx(self) -> int:
        start = self.counter + 2
        end = start + self.lx
        return chi(int.from_bytes(self.program.zeta[start:end], "little"), self.lx)

    @property
    def vy(self) -> int:
        start = self.counter + 2 + self.lx
        end = start + self.ly
        return chi(int.from_bytes(self.program.zeta[start:end], "little"), self.ly)

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            70: OpCode(
                name="store_imm_ind_u8",
                fn=cls.store_imm_ind_u(8),
                gas=1,
                is_terminating=False,
            ),
            71: OpCode(
                name="store_imm_ind_u16",
                fn=cls.store_imm_ind_u(16),
                gas=1,
                is_terminating=False,
            ),
            72: OpCode(
                name="store_imm_ind_u32",
                fn=cls.store_imm_ind_u(32),
                gas=1,
                is_terminating=False,
            ),
            73: OpCode(
                name="store_imm_ind_u64",
                fn=cls.store_imm_ind_u(64),
                gas=1,
                is_terminating=False,
            ),
        }

    @staticmethod
    def store_imm_ind_u(bitsize: int) -> Callable[[Any, list, Memory], OpReturn]:
        def store_u_impl(self, registers: list, memory: Memory) -> OpReturn:
            memory.write(
                registers[self.ra] + self.vx,
                int(self.vy % (2**bitsize)).to_bytes(bitsize // 8, "little"),
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory

        return store_u_impl
