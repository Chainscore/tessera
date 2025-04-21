from typing import Dict
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs1Imm1Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def lx(self) -> int:
        return min(4, max(0, self.skip_index - 1))
    
    @property
    def vx(self) -> int:
        start = self.counter+2
        end = start + self.lx
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], 
            self.lx
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            50: OpCode(name="jump_ind", fn=cls.jump_ind, gas=Gas(0), is_terminating=False),
            51: OpCode(name="load_imm", fn=cls.load_imm, gas=Gas(0), is_terminating=False),
        }

    def jump_ind(
        self, registers: Registers, memory: Memory
    ) -> OpReturn:
        status, counter = self.program.djump(self.counter, int(registers[self.ra] + self.vx) % 2**32)
        if status == CONTINUE:
            return status, counter, registers, memory 
        else:
            raise PvmError(PvmErrorCodes.PANIC)
            
    def load_imm(
        self, registers: Registers, memory: Memory
    ) -> OpReturn:
        """
        OPC20: Load a 64-bit immediate value into a register.
        """
        registers[self.ra] = Register(self.vx)
        return CONTINUE, self.skip_index, registers, memory