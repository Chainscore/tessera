from typing import Any, Tuple
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus, PvmError
from jam.types.protocol.core import Gas, ProgramCounter, RemainingGas

HostCallReturn = Tuple[ExecutionStatus, RemainingGas, Registers, Memory, Context]

class PsiH:

    @staticmethod
    def execute(
        blob: bytes,
        pc: ProgramCounter,
        gas: Gas,
        registers: Registers,
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
            result = dispatch_fn(
                status.value.register, Gas(remaining_gas), registers, memory, context
            )
            if isinstance(result, ExecutionStatus):
                return result, pc, remaining_gas, registers, memory
            
            status, remaining_gas, register, memory, context = result
            if status == ExecutionStatus.CONTINUE:
                return PsiH.execute(blob, pc, Gas(remaining_gas), registers, memory)
            elif remaining_gas < 0 or status == ExecutionStatus.OUT_OF_GAS:
                return ExecutionStatus.OUT_OF_GAS, pc, remaining_gas, registers, memory, context
            elif status == ExecutionStatus.PANIC:
                return result
            elif status == ExecutionStatus.HALT:
                return result
        else:
            raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")