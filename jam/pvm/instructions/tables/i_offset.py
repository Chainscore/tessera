from typing import Dict, Tuple
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, ExecutionStatus
from jam.pvm.utils import PvmUtilities
from jam.types.base.integers.fixed import U8
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec.primitives.integers import IntegerCodec


class WArgsOneOffset(InstructionTable):
    @property
    def lx(self) -> U8:
        return U8(min(4, int(self.skip_index)))
    
    @property
    def vx(self) -> U8:
        start = self.counter + 1
        end = start + self.lx
        return self.counter + PvmUtilities.to_signed(
            IntegerCodec.decode_from(int(self.lx), self.program.zeta[start:end])[0],
            self.lx,
        )
    
    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            40: OpCode(name="jump", fn=cls.jump, gas=Gas(0), is_terminating=False),
        }
    
    def jump(
        self, 
        registers: Registers, 
        memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]:
        status, updated_counter = self.program.branch(self.counter, self.vx, True)
        if status == CONTINUE:
            return CONTINUE, updated_counter, registers, memory
        else:
            raise PvmError(PvmErrorCodes.UNEXPECTED)