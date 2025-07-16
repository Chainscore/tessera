from typing import Dict
from jam.execution.pvm.status import PvmError, PANIC
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.instructions.instruction_table import InstructionTable


class InstructionsWoArgs(InstructionTable):
    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            0: OpCode(name="trap", fn=cls.trap, gas=1, is_terminating=True),
            1: OpCode(name="fallthrough", fn=cls.fallthrough, gas=1, is_terminating=True),
        }

    def trap(self, registers: list, memory: Memory) -> OpReturn:
        """
        OPC0: Trap the execution.
        """
        raise PvmError(PANIC)

    def fallthrough(self, registers: list, memory: Memory) -> OpReturn:
        """
        OPC1: Fall through to the next instruction.
        """
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
