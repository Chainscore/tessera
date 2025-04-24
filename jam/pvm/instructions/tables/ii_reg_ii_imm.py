from math import floor
from typing import Dict
from jam.pvm.instructions.code import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs2Reg2Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

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
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], 
            self.lx
        )
    
    @property
    def vy(self) -> int:
        start = self.counter + 3 + self.lx
        end = start + self.ly
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.ly, 
                self.program.zeta[start:end]
            )[0], 
            self.ly
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            180: OpCode(name="load_imm_jump_ind", fn=cls.load_imm_jump_ind, gas=Gas(0), is_terminating=True),
        }

    def load_imm_jump_ind(
            self, registers: Registers, memory: Memory
    ) -> OpReturn:
        wb = int(registers[self.rb])
        registers[self.ra] = Register(self.vx)
        status, counter = self.program.djump(
            self.counter,
            floor(wb + self.vy) % 2**32
        )
        return status, counter, registers, memory
    