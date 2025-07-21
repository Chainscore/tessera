from dataclasses import dataclass
from typing import Any, Callable, Tuple
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import ExecutionStatus

OpReturn = Tuple[ExecutionStatus, Any, list, Memory]


@dataclass
class OpCode:
    name: str
    fn: Callable[[Any, list, Memory], OpReturn]
    gas: int
    is_terminating: bool
