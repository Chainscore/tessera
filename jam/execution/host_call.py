import structlog
from typing import Any, Tuple
from jam.execution.invocations.protocol import Context, DispatchFunction
import os
from tsrkit_pvm import (
        ExecutionStatus,
        CONTINUE,
        PvmError,
        _HAS_RECOMPILER,
        _HAS_CYTHON,
)


_PVM_MODE = os.environ.get("PVM_MODE", "interpreter")
if _PVM_MODE == "interpreter":
    from tsrkit_pvm.cpvm.cy_memory import CyMemory as Memory
    from tsrkit_pvm.cpvm.cy_program import CyProgram as Program
    from tsrkit_pvm.cpvm.cy_pvm import CyInterpreter as PVM
elif _PVM_MODE == "mypyc":
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program, Interpreter as PVM 
elif _PVM_MODE == "recompiler" and _HAS_RECOMPILER:
    from tsrkit_pvm import REC_Memory as Memory, REC_Program as Program, Recompiler as PVM
else:
    raise ImportError(f"PVM mode {_PVM_MODE} is not supported")

HostCallReturn = Tuple[ExecutionStatus, int, int, list, Memory, Context]

logger = structlog.get_logger("pvm")

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
        current_gas = gas
        current_pc = pc

        host_calls = set()

        while True:
            # Direct PVM execution call
            logger.debug("TYPES", pr=type(program), pc=type(current_pc), gs=type(current_gas),
                         rg=type(registers), rgs=registers)
            status, current_pc, remaining_gas, registers, memory = PVM.execute(
                program, current_pc, current_gas, registers, memory, logger
            )

            if status == ExecutionStatus.HALT:
                return status, current_pc, remaining_gas, registers, memory, context
            elif status == ExecutionStatus.PANIC:
                return status, current_pc, remaining_gas, registers, memory, context
            elif status == ExecutionStatus.OUT_OF_GAS:
                return status, current_pc, remaining_gas, registers, memory, context
            elif status == ExecutionStatus.PAGE_FAULT:
                return status, current_pc, remaining_gas, registers, memory, context
            elif status == ExecutionStatus.HOST:
                try:
                    host_register = int(status.value.register)
                    host_calls.add(host_register)

                    status, remaining_gas, registers, memory, context = dispatch_fn(
                        host_register, remaining_gas, registers, memory, context
                    )

                    if remaining_gas < 0:
                        return ExecutionStatus.OUT_OF_GAS, current_pc, remaining_gas, registers, memory, context

                    if status == CONTINUE:
                        current_gas = remaining_gas
                        # Continue loop directly
                    else:
                        return status, current_pc, remaining_gas, registers, memory, context

                except PvmError as e:
                    return e.code, current_pc, remaining_gas - 10, registers, memory, context
            else:
                raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")
