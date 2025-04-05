from typing import Dict, Tuple
from jam.pvm.instructions.code import OpCode
from jam.pvm.instructions.protocol import InstructionTable
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, ExecutionStatus
from jam.pvm.utils import PvmUtilities
from jam.types.base.integers.fixed import U8
from jam.utils.codec.primitives.integers import IntegerCodec


class WArgsOneOffset(InstructionTable):
    @property
    def lx(self) -> U8:
        return min(4, self.skip_index)
    
    @property
    def vx(self) -> U8:
        start = self.program_counter + 1
        end = start + self.lx
        return self.program_counter + PvmUtilities.to_signed(
            IntegerCodec.decode_from(self.lx, self.zeta[start:end])[0],
            self.lx,
        )
    
    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            40: OpCode(name="jump", fn=cls.jump, gas=0, is_terminating=False),
        }
    
    @staticmethod
    def jump(registers: Registers, memory: Memory) -> Tuple[ExecutionStatus, Registers, Memory]:
        return CONTINUE, registers, memory

