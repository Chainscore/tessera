from typing import Any, Tuple
from jam.execution.host_calls.host_call import HostCallReturn, PsiH
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.code import Code
from jam.execution.pvm.status import PANIC, ExecutionStatus, PvmError
from jam.types.protocol.core import Gas, ProgramCounter

ArgInvokeReturn = Tuple[Gas, ExecutionStatus | bytes, Context]

class PsiM:
    @staticmethod
    def execute(
        blob: bytes,
        pc: ProgramCounter,
        gas: Gas,
        arguments: bytes,
        dispatch_fn: DispatchFunction,
        context: Any
    ) -> ArgInvokeReturn:
        code = Code.decode_from(blob + arguments)
        if code is None:
            return Gas(0), PANIC, context
        return PsiM.R(
            gas,
            PsiH.execute(code.code, pc, gas, code.registers, code.memory, dispatch_fn, context)
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
                result = memory.read(registers[7], registers[8] - registers[7])
            except PvmError as e:
                if e.code == ExecutionStatus.PAGE_FAULT:
                    result = []
                else: 
                    raise e                
        else:
            result = ExecutionStatus.PANIC
        return u, result, context
