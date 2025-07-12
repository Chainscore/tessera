from typing import TYPE_CHECKING, Dict, Protocol, Tuple
from jam.execution.pvm.instructions.opcode import OpCode
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import ExecutionStatus

if TYPE_CHECKING:
    from jam.execution.pvm.program import Program


class InstructionTable(Protocol):
    """
    A protocol for instruction tables.
    Defines a context for executing an instruction from an instruction table
    """

    counter: int
    program: "Program"

    # Constructor
    def __init__(self, counter: int, program: "Program"):
        self.counter = counter
        self.program = program

    @property
    def skip_index(self):
        return self.program.skip(self.counter)

    @classmethod
    def table(cls) -> Dict[int, OpCode]: ...

    # Execute the instruction
    def execute(
        self, opcode: int, registers: list, memory: Memory
    ) -> Tuple[ExecutionStatus, int, list, Memory]:
        # Read the opcode from instruction table
        op = self.table()[opcode]
        # Raise an error if the opcode is not found
        if op is None:
            raise ValueError(f"Invalid opcode: {self.program.zeta[self.counter]}")
        # Execute the instruction
        return op.fn(self, registers, memory)
