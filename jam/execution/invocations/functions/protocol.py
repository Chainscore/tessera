from typing import Dict, Protocol
from tsrkit_pvm import Memory, ExecutionStatus


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
    def execute(cls, host_call: int, gas: int, registers: list, memory: Memory, context, args):
        call = cls.HANDLERS[host_call]
        if gas < 0:
            return ExecutionStatus.OUT_OF_GAS, gas, registers, memory, context
        gas = gas - cls.HANDLERS[host_call]["gas"]
        return call["execute"](gas=gas, registers=registers, memory=memory, context=context, **args)
