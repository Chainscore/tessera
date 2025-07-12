from typing import Any, Callable, Dict

from jam.execution.pvm.utils import chi
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs2Imm(InstructionTable):
    @property
    def lx(self) -> int:
        return min(4, self.program.zeta[self.counter + 1])

    @property
    def ly(self) -> int:
        return min(4, max(0, self.skip_index - int(self.lx) - 1))

    @property
    def vx(self) -> int:
        start = self.counter + 2
        end = start + self.lx
        val = int.from_bytes(self.program.zeta[start:end], "little")
        return chi(
            val,
            self.lx,
        )

    @property
    def vy(self) -> int:
        start = self.counter + 2 + self.lx
        end = start + self.ly
        val = int.from_bytes(self.program.zeta[start:end], "little")
        return chi(
            val,
            self.ly,
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            30: OpCode(
                name="store_imm_u8", fn=cls.store_imm(8), gas=1, is_terminating=False
            ),
            31: OpCode(
                name="store_imm_u16", fn=cls.store_imm(16), gas=1, is_terminating=False
            ),
            32: OpCode(
                name="store_imm_u32", fn=cls.store_imm(32), gas=1, is_terminating=False
            ),
            33: OpCode(
                name="store_imm_u64", fn=cls.store_imm(64), gas=1, is_terminating=False
            ),
        }

    @staticmethod
    def store_imm(bit_size: int) -> Callable[[Any, list, Memory], OpReturn]:
        """Store an immediate value into memory. Implements the store_imm_u8, store_imm_u16, store_imm_u32, and store_imm_u64 instructions.

        Args:
            bit_size (int): The bit size of the immediate value to store. Could be 8 for storing u8, 16 for u16, etc.

        Returns:
            Callable[[Registers, Memory], Tuple[ExecutionStatus, Registers, Memory]]: The function to store the immediate value into memory.
        """

        def store_imm_impl(self, registers: list, memory: Memory) -> OpReturn:
            memory.write(
                self.vx, int(self.vy % 2**bit_size).to_bytes(bit_size // 8, "little")
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory

        return store_imm_impl
