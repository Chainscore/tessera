from typing import Dict, Protocol, Tuple
from jam.pvm.instructions.code import OpCode
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatus
from jam.pvm.zeta import Zeta
from jam.types.base.integers.fixed import U8


class InstructionTable(Protocol):
    """
    A protocol for instruction tables.
    """
    zeta: Zeta
    skip_index: U8
    program_counter: U8
    # Constructor
    def __init__(self, zeta: Zeta, skip_index: U8, program_counter: U8):
        self.zeta = zeta
        self.skip_index = skip_index
        self.program_counter = program_counter

    @classmethod
    def table(cls) -> Dict[int, OpCode]: 
        ...
    
    # Execute the instruction
    def execute(
        self, registers: Registers, memory: Memory
    ) -> Tuple[ExecutionStatus, Registers, Memory]:
        # Read the opcode from instruction table
        opcode = self.table()[self.zeta[self.program_counter].value]
        # Raise an error if the opcode is not found
        if opcode is None:
            raise ValueError(f"Invalid opcode: {self.zeta[self.program_counter].value}")
        # Execute the instruction
        return opcode.fn(self, registers, memory)