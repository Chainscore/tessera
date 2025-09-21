import time
from typing import Any, Tuple
from jam.execution.host_call import HostCallReturn, PsiH
from jam.execution.invocations.protocol import Context, DispatchFunction
from tsrkit_pvm import PANIC, ExecutionStatus, y_function
from tsrkit_types.bytes import Bytes
from jam.types.protocol.core import Gas
from jam.log_setup import pvm_logger as logger

ArgInvokeReturn = Tuple[Gas, ExecutionStatus | bytes, Context]


class PsiM:
    @staticmethod
    def execute(
        blob: Bytes | bytes,
        pc: int,
        gas: Gas,
        arguments: bytes,
        dispatch_fn: DispatchFunction,
        context: Any,
    ) -> ArgInvokeReturn:
        try:
            program, registers, memory = y_function(blob, arguments)

        except Exception as e:
            logger.error(
                "Failed to initialize the program",
                error=str(e),
                error_type=type(e).__name__,
            )
            return Gas(0), PANIC, context
        
        # Direct execution without intermediate R call
        host_result = PsiH.execute(program, pc, int(gas), registers, memory, dispatch_fn, context)
        return PsiM.R(gas, host_result)


    @staticmethod
    def R(g: Gas, grouped: HostCallReturn) -> ArgInvokeReturn:
        status, pc, remaining_gas, registers, memory, context = grouped
        
        # Fast path calculations
        consumed_gas = Gas(g - max(remaining_gas, 0))

        # Optimized status handling
        if status == ExecutionStatus.OUT_OF_GAS:
            result = status
            logger.warning("Invocation ran out of gas", initial_gas=int(g), consumed_gas=int(consumed_gas))
        elif status == ExecutionStatus.HALT:
            # Fast path for memory access check
            reg7, reg8 = int(registers[7]), int(registers[8])
            if memory.is_accessible(reg7, reg8):
                result = memory.read(reg7, reg8)
                logger.debug(
                    "Invocation halted with result",
                    res_mem_addr=reg7,
                    result_size=reg8,
                    result_hex=(
                        result.hex()[:32] + "..." if len(result.hex()) > 32 else result.hex()
                    ),
                    memory_addr=reg7,
                    memory_size=reg8,
                )
            else:
                result = bytes(0)
                logger.warning(
                    "Invocation halted but result memory not accessible",
                    memory_addr=reg7,
                    memory_size=reg8,
                )
        else:
            result = ExecutionStatus.PANIC
            logger.error(
                "Invocation ended with panic",
                status=str(status),
                final_pc=pc,
                consumed_gas=int(consumed_gas),
            )

        logger.info(
            "Invocation completed",
            status=str(status._value_),
            initial_gas=int(g),
            consumed_gas=int(consumed_gas),
            result_type=type(result).__name__,
        )

        return consumed_gas, result, context
