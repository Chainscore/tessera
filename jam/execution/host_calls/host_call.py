from typing import Any, Tuple
from jam.execution.host_calls.invocations.protocol import Context, DispatchFunction
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.program import Program
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus, PvmError
from jam.types.protocol.core import Gas, ProgramCounter, RemainingGas

HostCallReturn = Tuple[ExecutionStatus, ProgramCounter, RemainingGas, Registers, Memory, Context]

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
        print(f"PVM Exit {status}")
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
                    int(status.register.get_value()), Gas(remaining_gas), registers, memory, context
                )
                if remaining_gas < 0 or status == ExecutionStatus.OUT_OF_GAS:
                    return ExecutionStatus.OUT_OF_GAS, pc, remaining_gas, registers, memory, context
                if status == ExecutionStatus.PANIC:
                    return status, pc, remaining_gas, register, memory, context
                elif status == ExecutionStatus.HALT:
                    return status, pc, remaining_gas, register, memory, context
                elif status == ExecutionStatus.CONTINUE:
                    program, _ = Program.decode_from(blob)
                    return PsiH.execute(blob, pc, Gas(remaining_gas), registers, memory, dispatch_fn, context)
                else:
                    status, pc, remaining_gas, registers, memory, context
            except PvmError as e:
                return e.code, pc, remaining_gas, registers, memory, context
        else:
            raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")