from dataclasses import dataclass
from typing import Tuple, List

from jam.config.logging import get_logger, log_performance
from jam.execution.pvm.instructions.table_map import InstTableMap
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.program import Program
from jam.execution.pvm.status import OUT_OF_GAS, PAGE_FAULT, PANIC, ExecutionStatus, PvmError, CONTINUE

# Module-specific logger
logger = get_logger("pvm")

@dataclass
class PVM:

    @classmethod
    def execute(
        cls,
        blob: bytes,
        program_counter: int,
        gas: int,
        registers: List[int],
        memory: Memory
    ) -> Tuple[ExecutionStatus, int, int, list, Memory]:
        """
        Execute the program blob `p` as per Psi specification.

        Args:
            blob: Program blob
            program_counter: Initial program counter
            gas: Gas provided for execution
            registers: Initial registers
            memory: Initial memory

        Returns:
            ExecutionStatus: Status of the execution - Either PANIC, HALT, PAGE-FAULT, HOST, OUT-OF-GAS, or CONTINUE
            U32: Final program counter
            RemainingGas: Remaining gas
            Registers: Final registers
            Memory: Final memory
        """
        program, _ = Program.decode_from(blob)
        remaining_gas = int(gas)
        registers = [int(reg) for reg in registers]
        program_counter = int(program_counter)
        
        execution_context = {
            "blob_size": len(blob),
            "initial_pc": program_counter,
            "initial_gas": gas,
            "program_size": len(program.zeta) if hasattr(program, 'zeta') else 0,
        }
        
        logger.debug(
            "Starting PVM execution",
            **execution_context,
            registers=registers,
        )
        
        instruction_count = 0

        while True:
            try:
                if program_counter >= len(program.zeta):
                    logger.error(
                        "Program counter exceeded program size",
                        pc=program_counter,
                        program_size=len(program.zeta),
                        **execution_context
                    )
                    status = PANIC
                    break

                opcode = program.zeta[program_counter]
                table = InstTableMap.get_instructions_table(opcode)(counter=program_counter, program=program)

                # Log detailed execution info only at DEBUG level
                logger.debug(
                    "Executing instruction",
                    pc=program_counter,
                    opcode=opcode,
                    instruction=table.table()[opcode].name,
                    table=table.__class__.__name__,
                    gas_remaining=remaining_gas,
                    gas_cost=table.table()[opcode].gas,
                    registers=registers,
                )

                status, program_counter, registers, memory = table.execute(opcode, registers, memory)
                remaining_gas -= int(table.table()[opcode].gas)
                instruction_count += 1

                # Check for out of gas
                if remaining_gas < 0:
                    logger.warning(
                        "PVM execution ran out of gas",
                        instructions_executed=instruction_count,
                        final_pc=program_counter,
                        gas_deficit=abs(remaining_gas),
                        **execution_context
                    )
                    status = OUT_OF_GAS
                    break

                # Check for completion conditions
                elif status == ExecutionStatus.HALT:
                    logger.info(
                        "PVM execution halted normally",
                        instructions_executed=instruction_count,
                        final_pc=program_counter,
                        gas_remaining=remaining_gas,
                        **execution_context
                    )
                    break
                elif status == ExecutionStatus.HOST:
                    logger.debug(
                        "PVM execution paused for host call",
                        instructions_executed=instruction_count,
                        pc=program_counter,
                        gas_remaining=remaining_gas,
                        **execution_context
                    )
                    break

            except PvmError as e:
                logger.error(
                    "PVM execution error",
                    error_code=e.code,
                    error_message=str(e),
                    instructions_executed=instruction_count,
                    pc=program_counter,
                    gas_remaining=remaining_gas,
                    **execution_context
                )

                if e.code == PANIC:
                    status = PANIC
                    break
                elif e.code == ExecutionStatus.PAGE_FAULT:
                    status = PAGE_FAULT(e.code.value.register)
                    break
                else:
                    raise e
            except Exception as e:
                logger.critical(
                    "Unexpected PVM execution error",
                    error=str(e),
                    error_type=type(e).__name__,
                    instructions_executed=instruction_count,
                    pc=program_counter,
                    **execution_context
                )
                raise e

        logger.info(
            "PVM execution completed",
            status=str(status),
            instructions_executed=instruction_count,
            final_pc=program_counter,
            gas_remaining=remaining_gas,
            gas_used=gas - remaining_gas,
            **execution_context
        )
        
        return status, program_counter, remaining_gas, registers, memory
