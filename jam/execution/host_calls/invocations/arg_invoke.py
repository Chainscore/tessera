from typing import Any, Tuple
from jam.execution.host_calls.host_call import HostCallReturn, PsiH
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.code import y_function
from jam.execution.pvm.status import PANIC, ExecutionStatus
from jam.types.base import Bytes
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec import DecodeError

ArgInvokeReturn = Tuple[Gas, ExecutionStatus | bytes, Context]

class PsiM:
    @staticmethod
    def execute(
        blob: Bytes|bytes,
        pc: int,
        gas: Gas,
        arguments: bytes,
        dispatch_fn: DispatchFunction,
        context: Any
    ) -> ArgInvokeReturn:
        try:
            code, registers, memory = y_function(bytes(Bytes(blob)), arguments)
        except DecodeError:
            return Gas(0), PANIC, context
        return PsiM.R(
            gas,
            PsiH.execute(code, pc, int(gas), registers, memory, dispatch_fn, context)
        )

    @staticmethod
    def R(g: Gas, grouped: HostCallReturn) -> ArgInvokeReturn:
        status, pc, remaining_gas, registers, memory, context = grouped
        result: ExecutionStatus | bytes = bytes(0)
        u = Gas(g - max(int(remaining_gas), 0))
        if status == ExecutionStatus.OUT_OF_GAS:
            result = ExecutionStatus.OUT_OF_GAS
        elif status == ExecutionStatus.HALT:
            if memory.is_accessible(int(registers[7]), int(registers[8])):
                result = memory.read(int(registers[7]), int(registers[8]))
        else:
            result = ExecutionStatus.PANIC

        print(f"Execution output >> Gas consumed {u} | Result {result} ")
        return u, result, context
