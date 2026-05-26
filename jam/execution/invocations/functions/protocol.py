from typing import Dict, Protocol, Any
from tsrkit_pvm import ExecutionStatus


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
    def execute(cls, host_call: int, gas: int, registers: list, memory: Any, context, args):
        if gas < 0:
            return ExecutionStatus.OUT_OF_GAS, gas, registers, memory, context
        call = cls.HANDLERS[host_call]
        gas -= call["gas"]
        if gas < 0:
            return ExecutionStatus.OUT_OF_GAS, gas, registers, memory, context
        
        return call["execute"](gas=gas, registers=registers, memory=memory, context=context, **args)
