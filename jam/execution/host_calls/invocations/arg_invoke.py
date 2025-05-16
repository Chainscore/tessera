from typing import Any, Tuple
from jam.execution.host_calls.host_call import HostCallReturn, PsiH
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.code import y_function
from jam.execution.pvm.status import PANIC, ExecutionStatus, PvmError
from jam.types.base import Bytes
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec import DecodeError

ArgInvokeReturn = Tuple[Gas, ExecutionStatus | bytes, Context]

class PsiM:
    @staticmethod
    def execute(
        blob: Bytes,
        pc: ProgramCounter,
        gas: Gas,
        arguments: bytes,
        dispatch_fn: DispatchFunction,
        context: Any
    ) -> ArgInvokeReturn:
        try:
            code, registers, memory = y_function(bytes(Bytes(blob)), arguments)
            print(f"Registers: {registers}")
        except DecodeError:
            return Gas(0), PANIC, context
        return PsiM.R(
            gas,
            PsiH.execute(code, pc, gas, registers, memory, dispatch_fn, context)
        )

    @staticmethod
    def R(g: Gas, grouped: HostCallReturn) -> ArgInvokeReturn:
        status, pc, remaining_gas, registers, memory, context = grouped
        result = Any
        u = g - max(int(remaining_gas), 0)
        if status == ExecutionStatus.OUT_OF_GAS:
            result = ExecutionStatus.OUT_OF_GAS
        elif status == ExecutionStatus.HALT:
            try:
                result = memory.read(int(registers[7]), int(registers[8]))
            except PvmError as e:
                if e.code == ExecutionStatus.PAGE_FAULT:
                    result = []
                else: 
                    raise e
        else:
            result = ExecutionStatus.PANIC
        return u, result, context
