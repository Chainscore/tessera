from typing import Any, Tuple
from jam.execution.invocations.protocol import Context, DispatchFunction
import os
from jam.log_setup import pvm_logger as logger
from tsrkit_pvm import (
        ExecutionStatus,
        CONTINUE,
        PvmError,
        _HAS_RECOMPILER,
        _HAS_CYTHON,
)


_PVM_MODE = os.environ.get("PVM_MODE", "interpreter")
if _PVM_MODE == "interpreter":
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program, Interpreter as PVM 
elif _PVM_MODE == "cython" and _HAS_CYTHON:
    from tsrkit_pvm.cpvm.cy_pvm import CyInterpreter as PVM
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program
elif _PVM_MODE == "recompiler" and _HAS_RECOMPILER:
    from tsrkit_pvm import REC_Memory as Memory, REC_Program as Program, Recompiler as PVM
else:
    raise ImportError(f"PVM mode {_PVM_MODE} is not supported")

HostCallReturn = Tuple[ExecutionStatus, int, int, list, Memory, Context]


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
        # Ultra-optimized execution loop with minimal overhead
        current_gas = gas
        current_pc = pc
        
        # Main execution loop with aggressive optimization
        while True:
            # Direct PVM execution call
            status, current_pc, remaining_gas, registers, memory = PVM.execute(
                program, current_pc, current_gas, registers, memory, logger
            )
            
            # Optimized terminal state checking with early returns
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
                    # Ultra-fast host call dispatch
                    host_register = int(status.value.register)
                    status, remaining_gas, registers, memory, context = dispatch_fn(
                        host_register, remaining_gas, registers, memory, context
                    )
                    
                    # Inline gas check for maximum performance
                    if remaining_gas < 0:
                        return ExecutionStatus.OUT_OF_GAS, current_pc, remaining_gas, registers, memory, context

                    # Direct continue check without function call overhead
                    if status == CONTINUE:
                        current_gas = remaining_gas
                        # Continue loop directly
                    else:
                        return status, current_pc, remaining_gas, registers, memory, context
                        
                except PvmError as e:
                    return e.code, current_pc, remaining_gas - 10, registers, memory, context
            else:
                raise PvmError(ExecutionStatus.PANIC, f"Invalid execution status {status}")
