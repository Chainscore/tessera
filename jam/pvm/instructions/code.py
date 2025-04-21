from dataclasses import dataclass
from typing import Any, Callable, Tuple
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatus
from jam.types.protocol.core import Gas, ProgramCounter

OpReturn = Tuple[ExecutionStatus, ProgramCounter, Registers, Memory]

@dataclass
class OpCode:
    name: str
    fn: Callable[[Any, Registers, Memory], OpReturn]
    gas: Gas
    is_terminating: bool


