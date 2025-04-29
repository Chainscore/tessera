from typing import Any, Callable, Literal, Protocol, Tuple, Union

from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, HALT, OUT_OF_GAS, PANIC, ExecutionStatus
from jam.types.protocol.core import Gas, Register

Context = Any
DispatchNormalReturn = Tuple[Union[CONTINUE, HALT, PANIC, OUT_OF_GAS], Gas, Registers, Memory, Context]
DispatchReturn = Union[
    DispatchNormalReturn,
    ExecutionStatus.PAGE_FAULT
]

DispatchFunction = Callable[[Register, Gas, Registers, Memory, Context], DispatchReturn]


class InvocationProtocol(Protocol):
    def execute(self): ...
    def dispatch(self) -> DispatchReturn: ...
