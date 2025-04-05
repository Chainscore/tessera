from typing import Dict, Tuple
from jam.pvm.instructions.code import OpCode
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import HOST, ExecutionStatus
from jam.pvm.utils import PvmUtilities
from jam.types.base.integers.fixed import U8
from jam.pvm.instructions.protocol import InstructionTable
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs1Imm(InstructionTable):
    @property
    def lx(self) -> U8:
        return min(4, self.skip_index)

    @property
    def vx(self) -> U8:
        codec = IntegerCodec(self.lx)
        return PvmUtilities.chi(
            codec.decode_from(
                self.zeta[self.program_counter + 1 : self.program_counter + self.skip_index + 1]
            ),
            self.lx,
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            10: OpCode(name="ecalli", fn=cls.ecalli, gas=0, is_terminating=False),
        }

    def ecalli(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, Registers, Memory]:
        """
        OPC10: Ecalli.
        """
        return HOST(self.vx), registers, memory
