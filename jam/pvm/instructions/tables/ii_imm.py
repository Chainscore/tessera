from http.client import CONTINUE
from typing import Callable, Dict, Tuple
from jam.pvm.instructions.code import OpCode
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatus
from jam.pvm.utils import PvmUtilities
from jam.types.base.integers.fixed import U8
from jam.pvm.instructions.protocol import InstructionTable
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs2Imm(InstructionTable):
    @property
    def lx(self) -> U8:
        return min(4, self.zeta[self.program_counter + 1])
    
    @property
    def ly(self) -> U8:
        return min(4, max(0, self.skip_index - int(self.lx) - 1))
    
    @property
    def vx(self) -> int:
        start = self.program_counter + 2
        end = start + self.lx
        val, _ = IntegerCodec.decode_from(int(self.lx), self.zeta[start:end])
        return PvmUtilities.chi(
            val,
            self.lx,
        )

    @property
    def vy(self) -> int:
        start = self.program_counter + 2 + self.lx
        end = start + self.ly
        val, _ = IntegerCodec.decode_from(int(self.ly), self.zeta[start:end])
        return PvmUtilities.chi(
            val,
            self.ly,
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            30: OpCode(name="store_imm_u8", fn=cls.store_imm(8), gas=0, is_terminating=False),
            31: OpCode(name="store_imm_u16", fn=cls.store_imm(16), gas=0, is_terminating=False),
            32: OpCode(name="store_imm_u32", fn=cls.store_imm(32), gas=0, is_terminating=False),
            33: OpCode(name="store_imm_u64", fn=cls.store_imm(64), gas=0, is_terminating=False),
        }
    
    @staticmethod
    def store_imm(bit_size: int) -> Callable[[Registers, Memory], Tuple[ExecutionStatus, Registers, Memory]]:
        """Store an immediate value into memory. Implements the store_imm_u8, store_imm_u16, store_imm_u32, and store_imm_u64 instructions.

        Args:
            bit_size (int): The bit size of the immediate value to store. Could be 8 for storing u8, 16 for u16, etc.

        Returns:
            Callable[[Registers, Memory], Tuple[ExecutionStatus, Registers, Memory]]: The function to store the immediate value into memory.
        """
        def store_imm_impl(
            self, registers: Registers, memory: Memory
        ) -> Tuple[ExecutionStatus, Registers, Memory]:
            memory.write(self.vx, IntegerCodec(bit_size // 8).encode(self.vy % 2**bit_size))
            return CONTINUE, registers, memory
        return store_imm_impl
