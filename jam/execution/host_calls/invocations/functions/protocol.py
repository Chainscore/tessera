from typing import Callable, Dict, Protocol
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus
from jam.types.protocol.core import Gas, Register


class InvocationFunctions(Protocol):
    HANDLERS: Dict[int, Dict] = {}

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
    def execute(cls, host_call: int, gas: Gas, registers: Registers, memory: Memory, context, args):
        call = cls.HANDLERS[host_call]
        if gas < call['gas']:
            return ExecutionStatus.OUT_OF_GAS, gas, registers, memory, context
        gas = gas - cls.HANDLERS[host_call]['gas']
        return call['execute'](gas=gas, registers=registers, memory=memory, context=context, **args)