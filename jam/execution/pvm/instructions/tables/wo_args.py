from typing import Dict, Tuple
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.opcode import OpCode
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatus, CONTINUE
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, ProgramCounter


class InstructionsWoArgs(InstructionTable):
    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            0: OpCode(name="trap", fn=cls.trap, gas=Gas(1), is_terminating=True),
            1: OpCode(name="fallthrough", fn=cls.fallthrough, gas=Gas(1), is_terminating=True),
        }

    def trap(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]:
        """
        OPC0: Trap the execution.
        """
        raise PvmError(PvmErrorCodes.PANIC)

    def fallthrough(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]:
        """
        OPC1: Fall through to the next instruction.
        """
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
