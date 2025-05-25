from typing import Any, Callable, Dict

from jam.execution.pvm.utils import chi, z, compare
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWArgs1Reg1Imm1Offset(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def lx(self) -> int:
        return min(4, (int(self.program.zeta[self.counter + 1]) // 16) % 8)
    
    @property
    def ly(self) -> int:
        return min(4, max(0, int(self.skip_index) - self.lx - 1))
    
    @property
    def vx(self) -> int:
        start = self.counter + 2
        end = start + self.lx
        return chi(
            int.from_bytes(
                self.program.zeta[start:end],
                "little"
            ),
            self.lx
        )
    
    @property
    def vy(self) -> int:
        start = self.counter + 2 + self.lx
        end = start + self.ly
        return int(self.counter) + z(
            int.from_bytes(
                self.program.zeta[start:end],
                "little"
            ),
            self.ly
        )

    @classmethod
    def table(cls) -> Dict[int,OpCode]:
        return {
            80: OpCode(name="load_imm_jump", fn=cls.load_imm_jump, gas=1, is_terminating=True),
            81: OpCode(name="branch_eq_imm", fn=cls.branch_imm("eq"), gas=1, is_terminating=True),
            82: OpCode(name="branch_ne_imm", fn=cls.branch_imm("ne"), gas=1, is_terminating=True),
            83: OpCode(name="branch_lt_u_imm", fn=cls.branch_imm("lt"), gas=1, is_terminating=True),
            84: OpCode(name="branch_le_u_imm", fn=cls.branch_imm("le"), gas=1, is_terminating=True),
            85: OpCode(name="branch_ge_u_imm", fn=cls.branch_imm("ge"), gas=1, is_terminating=True),
            86: OpCode(name="branch_gt_u_imm", fn=cls.branch_imm("gt"), gas=1, is_terminating=True),
            87: OpCode(name="branch_lt_s_imm", fn=cls.branch_imm("lt", True), gas=1, is_terminating=True),
            88: OpCode(name="branch_le_s_imm", fn=cls.branch_imm("le", True), gas=1, is_terminating=True),
            89: OpCode(name="branch_ge_s_imm", fn=cls.branch_imm("ge", True), gas=1, is_terminating=True),
            90: OpCode(name="branch_gt_s_imm", fn=cls.branch_imm("gt", True), gas=1, is_terminating=True),
        }

    def load_imm_jump(self, registers: list, memory: Memory) -> OpReturn:
        registers[self.ra] = self.vx
        status, counter = self.program.branch(self.counter, self.vy, True)
        if status == CONTINUE and counter != self.counter:
            return status, counter, registers, memory
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    @staticmethod
    def branch_imm(op: str, signed = False) -> Callable[[Any, list, Memory], OpReturn]:
        def branch_u_imm_impl(
                self, registers: list, memory: Memory
        ) -> OpReturn:
            status, counter = self.program.branch(
                self.counter, 
                self.vy, 
                compare(
                    z(registers[self.ra], 8) if signed else registers[self.ra],
                    z(self.vx, 8) if signed else self.vx,
                    op
                )
            )
            if status == CONTINUE and counter != self.counter:
                return status, counter, registers, memory
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return branch_u_imm_impl