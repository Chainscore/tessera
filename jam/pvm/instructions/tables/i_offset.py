from typing import Dict, Tuple
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, ExecutionStatus
from jam.pvm.utils import PvmUtilities
from jam.types.base.integers.fixed import U32, U8
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec.primitives.integers import IntegerCodec


class WArgsOneOffset(InstructionTable):
    @property
    def lx(self) -> int:
        return min(4, int(self.skip_index))
    
    @property
    def vx(self) -> int:
        start = self.counter + 1
        end = start + self.lx
        print(self.program.zeta[start:end], IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], self.lx)
        return int(self.counter) + PvmUtilities.z(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0],
            self.lx
        )
    
    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            40: OpCode(name="jump", fn=cls.jump, gas=Gas(1), is_terminating=True),
        }
    
    def jump(
        self, 
        registers: Registers, 
        memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]:
        status, counter = self.program.branch(self.counter, U32(self.vx), True)
        if status == CONTINUE and counter != self.counter:
            return status, counter, registers, memory
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory