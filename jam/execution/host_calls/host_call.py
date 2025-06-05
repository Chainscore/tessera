from typing import Any, Tuple

from jam.execution.pvm.status import CONTINUE
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.status import ExecutionStatus, PvmError

HostCallReturn = Tuple[ExecutionStatus, int, int, list, Memory, Context]

class PsiH:

    @staticmethod
    def execute(
        blob: bytes,
        pc: int,
        gas: int,
        registers: list,
        memory: Memory,
        dispatch_fn: DispatchFunction,
        context: Any
    ) -> HostCallReturn:
        status, pc, remaining_gas, registers, memory = PVM.execute(blob, pc, gas, registers, memory)
        if (
            status == ExecutionStatus.PANIC
            or status == ExecutionStatus.OUT_OF_GAS
            or status == ExecutionStatus.PAGE_FAULT
            or status == ExecutionStatus.HALT
        ):
            return status, pc, remaining_gas, registers, memory, context
        elif status == ExecutionStatus.HOST:
            print("Host call >>", status.value.register)
            try:
                status, remaining_gas, register, memory, context = dispatch_fn(
                    int(status.value.register), remaining_gas, registers, memory, context
                )
                if remaining_gas < 0:
                    status = ExecutionStatus.OUT_OF_GAS

                if status == CONTINUE:
                    return PsiH.execute(blob, pc, remaining_gas, registers, memory, dispatch_fn, context)
                return status, pc, remaining_gas, registers, memory, context
            except PvmError as e:
                return e.code, pc, remaining_gas, registers, memory, context
        else:
            raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")