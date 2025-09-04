from typing import Any, Tuple
from jam.execution.invocations.protocol import Context, DispatchFunction
import os

from jam.logging import get_logger 

if os.environ.get("PVM_MODE") == "recompiler":
    from tsrkit_pvm import REC_Memory as Memory, REC_Program as Program, Recompiler as PVM
else:
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program, Interpreter as PVM 

from tsrkit_pvm import (
        ExecutionStatus,
        CONTINUE,
        PvmError,
)
HostCallReturn = Tuple[ExecutionStatus, int, int, list, Memory, Context]

logger = get_logger("pvm")

class PsiH:
    @staticmethod
    def execute(
        program: Program,
        pc: int,
        gas: int,
        registers: list,
        memory: Memory,
        dispatch_fn: DispatchFunction,
        context: Any,
    ) -> HostCallReturn:
        status, pc, remaining_gas, registers, memory = PVM.execute(
            program, pc, gas, registers, memory, logger
        )
        if (
            status == ExecutionStatus.PANIC
            or status == ExecutionStatus.OUT_OF_GAS
            or status == ExecutionStatus.PAGE_FAULT
            or status == ExecutionStatus.HALT
        ):
            return status, pc, remaining_gas, registers, memory, context
        elif status == ExecutionStatus.HOST:
            try:
                status, remaining_gas, register, memory, context = dispatch_fn(
                    int(status.value.register),
                    remaining_gas,
                    registers,
                    memory,
                    context,
                )
                if remaining_gas < 0:
                    status = ExecutionStatus.OUT_OF_GAS

                if status == CONTINUE:
                    return PsiH.execute(
                        program,
                        pc,
                        remaining_gas,
                        registers,
                        memory,
                        dispatch_fn,
                        context,
                    )
                return status, pc, remaining_gas, registers, memory, context
            except PvmError as e:
                return e.code, pc, remaining_gas, registers, memory, context
        else:
            raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")
