from typing import Dict, Tuple
from jam.pvm.instructions.code import OpCode
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, ExecutionStatus
from jam.types.base.integers.fixed import U64, U8
from jam.pvm.instructions.protocol import InstructionTable


class InstructionsWArgs1Imm1EwImm(InstructionTable):
    @property
    def ra(self) -> U8:
        return min(12, self.zeta[self.program_counter + 1] % 16)

    @property
    def vx(self) -> U64:
        value, _ = U64.decode_from(bytes(self.zeta[self.program_counter + 2 : self.program_counter + 10]))
        return value

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            20: OpCode(name="load_imm_64", fn=cls.load_imm_64, gas=0, is_terminating=False)
        }

    def load_imm_64(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, Registers, Memory]:
        """
        OPC20: Load a 64-bit immediate value into a register.
        """
        _vx = self.vx
        registers[self.ra] = _vx
        return CONTINUE, registers, memory