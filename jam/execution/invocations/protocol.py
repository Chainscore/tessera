from typing import Any, Callable, Dict, Protocol, Tuple

from jam.logging import get_logger
from jam.execution.invocations.functions.protocol import InvocationFunctions
from tsrkit_pvm import (
    CONTINUE,
    HALT,
    OUT_OF_GAS,
    PANIC,
    ExecutionStatus,
    HostStatus,
)
from jam.types.protocol.core import Gas, Register

Context = Any
MemoryLike = Any
DispatchReturn = Tuple[ExecutionStatus, Gas, list, MemoryLike, Context]

DispatchFunction = Callable[[Register, Gas, list, MemoryLike, Context], DispatchReturn]


InvocationInfo = Tuple[InvocationFunctions, Tuple]

logger = get_logger("host_calls")


class InvocationProtocol(Protocol):
    table: Dict[int, InvocationInfo]
    
    def execute(self):
        """Starting point of execution"""
        ...

    def dispatch(
        self, host_call: int, gas: int, registers: list, memory: MemoryLike, x: Context
    ) -> DispatchReturn:
        # Fast path for invalid host calls with minimal overhead
        table_entry = self.table.get(host_call)
        if table_entry is None:
            registers[7] = HostStatus.WHAT.value
            return ExecutionStatus.CONTINUE, gas - 10, registers, memory, x
        
        # Direct unpacking and execution
        dispatch_fn_calls, args = table_entry
        
        # Direct execution without intermediate steps
        return dispatch_fn_calls.execute(
            host_call,
            gas=gas,
            registers=registers,
            memory=memory,
            context=x,
            args=args,
        )
