from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Callable, Dict, Protocol, Tuple, Union
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, HALT, OUT_OF_GAS, PANIC, ExecutionStatus, HostStatus, PAGE_FAULT, \
    PvmError
from jam.types.protocol.core import Gas, Register

Context = Any
DispatchNormalReturn = Tuple[Union[CONTINUE, HALT, PANIC, OUT_OF_GAS], Gas, Registers, Memory, Context]
DispatchReturn = Union[
    DispatchNormalReturn,
    ExecutionStatus.PAGE_FAULT
]

DispatchFunction = Callable[[Register, Gas, Registers, Memory, Context], DispatchReturn]


InvocationInfo = Tuple[
    InvocationFunctions,
    Tuple
]

class InvocationProtocol(Protocol):
    def execute(self):
        """Starting point of execution"""
        ...

    def table(self) -> Dict[int, InvocationInfo]: ...

    def dispatch(self, host_call: int, gas: Gas, registers: Registers, memory: Memory, x: Context) -> DispatchReturn:
        if host_call not in self.table():
            registers[7] = Register(HostStatus.WHAT.value)
            return ExecutionStatus.CONTINUE, gas - 10, registers, memory, x
        info = self.table()[host_call]
        # print(f">> Host call: {host_call}")
        return info[0].execute(host_call, gas=gas, registers=registers, memory=memory, context=x, args=info[1])