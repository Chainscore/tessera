from typing import Callable, Dict, Protocol
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus
from jam.types.protocol.core import Gas, Register


class InvocationFunctions(Protocol):
    HANDLERS: Dict[str, ] = {}

    @classmethod
    def register(cls, host_call: int, gas_cost: int):
        def decorator(fn):
            cls.HANDLERS[host_call] = {
                "gas": gas_cost,
                "execute": fn,
            }
            return fn
        return decorator
    
    @classmethod
    def execute(cls, host_call: int, **kwargs):
        call = cls.table()[host_call]
        if kwargs.gas < call.gas:
            return ExecutionStatus.OUT_OF_GAS, kwargs.gas, kwargs.registers, kwargs.memory
        
        return call.execute(kwargs)