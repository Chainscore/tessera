from typing import Any, Tuple
from jam.execution.host_call import HostCallReturn, PsiH
from jam.execution.invocations.protocol import Context, DispatchFunction
from tsrkit_pvm import PANIC, ExecutionStatus, y_function
from tsrkit_types.bytes import Bytes
from jam.types.protocol.core import Gas
from jam.logging import get_logger

# Module-specific logger
logger = get_logger("host_calls")

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
        logger.debug(
            "Starting invocation",
            blob_size=len(blob),
            program_counter=pc,
            gas=int(gas),
            arguments_size=len(arguments),
            context_type=type(context).__name__,
        )

        try:
            program, registers, memory = y_function(bytes(Bytes(blob)), arguments, "")

        except Exception as e:
            logger.error(
                "Failed to initialize the program",
                error=str(e),
                error_type=type(e).__name__,
            )
            return Gas(0), PANIC, context
        
        return PsiM.R(
            gas,
            PsiH.execute(program, pc, int(gas), registers, memory, dispatch_fn, context),
        )


    @staticmethod
    def R(g: Gas, grouped: HostCallReturn) -> ArgInvokeReturn:
        status, pc, remaining_gas, registers, memory, context = grouped
        result: ExecutionStatus | bytes = bytes(0)
        u = Gas(g - max(int(remaining_gas), 0))

        logger.debug(
            "Processing invocation result",
            initial_gas=int(g),
            remaining_gas=remaining_gas,
            consumed_gas=int(u),
            status=str(status),
            final_pc=pc,
        )

        if status == ExecutionStatus.OUT_OF_GAS:
            result = status
            logger.warning("Invocation ran out of gas", initial_gas=int(g), consumed_gas=int(u))
        elif status == ExecutionStatus.HALT:
            if memory.is_accessible(int(registers[7]), int(registers[8])):
                result = memory.read(int(registers[7]), int(registers[8]))
                logger.debug(
                    "Invocation halted with result",
                    res_mem_addr=registers[7],
                    result_size=registers[8],
                    result_hex=(
                        result.hex()[:32] + "..." if len(result.hex()) > 32 else result.hex()
                    ),
                    memory_addr=int(registers[7]),
                    memory_size=int(registers[8]),
                )
            else:
                logger.warning(
                    "Invocation halted but result memory not accessible",
                    memory_addr=int(registers[7]),
                    memory_size=int(registers[8]),
                )
        else:
            result = ExecutionStatus.PANIC
            logger.error(
                "Invocation ended with panic",
                status=str(status),
                final_pc=pc,
                consumed_gas=int(u),
            )

        logger.info(
            "Invocation completed",
            status=str(status._value_),
            initial_gas=int(g),
            consumed_gas=int(u),
            result_type=type(result).__name__,
            result_size=len(result) if isinstance(result, bytes) else None,
        )

        return u, result, context
