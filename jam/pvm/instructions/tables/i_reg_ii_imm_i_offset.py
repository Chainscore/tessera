from typing import Any, Callable, Dict
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, PANIC
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec

def compare(a: int, b: int, op: str) -> bool:
    return getattr(a, f"__{op}__")(b)

class InstructionsWArgs1Reg2Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

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
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], 
            self.lx
        )
    
    @property
    def vy(self) -> int:
        start = self.counter + 2 + self.lx
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
            80: OpCode(name="load_imm_jump", fn=cls.load_imm_jump(8), gas=Gas(0), is_terminating=False),
            81: OpCode(name="branch_eq_imm", fn=cls.branch_imm("eq"), gas=Gas(0), is_terminating=False),
            82: OpCode(name="branch_ne_imm", fn=cls.branch_imm("ne"), gas=Gas(0), is_terminating=False),
            83: OpCode(name="branch_lt_u_imm", fn=cls.branch_imm("lt"), gas=Gas(0), is_terminating=False),
            84: OpCode(name="branch_le_u_imm", fn=cls.branch_imm("le"), gas=Gas(0), is_terminating=False),
            85: OpCode(name="branch_ge_u_imm", fn=cls.branch_imm("ge"), gas=Gas(0), is_terminating=False),
            86: OpCode(name="branch_gt_u_imm", fn=cls.branch_imm("gt"), gas=Gas(0), is_terminating=False),
            87: OpCode(name="branch_lt_s_imm", fn=cls.branch_imm("lt", True), gas=Gas(0), is_terminating=False),
            88: OpCode(name="branch_le_s_imm", fn=cls.branch_imm("le", True), gas=Gas(0), is_terminating=False),
            89: OpCode(name="branch_ge_s_imm", fn=cls.branch_imm("ge", True), gas=Gas(0), is_terminating=False),
            90: OpCode(name="branch_gt_s_imm", fn=cls.branch_imm("gt", True), gas=Gas(0), is_terminating=False),
        }

    def load_imm_jump(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = self.vx
        status, counter = self.program.branch(self.counter, self.vy, True)
        if status == CONTINUE:
            return status, counter, registers, memory
        else:
            return PANIC, self.counter, registers, memory

    @staticmethod
    def branch_imm(op: str, signed = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def branch_u_imm_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            status, counter = self.program.branch(
                self.counter, 
                self.vy, 
                compare(
                    PvmUtilities.to_signed(registers[self.ra]) if signed else registers[self.ra], 
                    PvmUtilities.to_signed(self.vx) if signed else self.vx, 
                    op
                )
            )
            if status == CONTINUE:
                return status, counter, registers, memory
            else:
                return PANIC, self.counter, registers, memory
        return branch_u_imm_impl