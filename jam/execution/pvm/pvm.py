import time
from dataclasses import dataclass
from typing import Tuple, List
from jam.logging import get_logger
from jam.execution.pvm.instructions.inst_map import inst_map
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.program import Program
from jam.execution.pvm.status import (
    OUT_OF_GAS,
    PAGE_FAULT,
    PANIC,
    ExecutionStatus,
    PvmError,
)

logger = get_logger("pvm")


@dataclass
class PVM:

    @classmethod
    def execute(
        cls,
        program: Program,
        program_counter: int,
        gas: int,
        registers: List[int],
        memory: Memory,
    ) -> Tuple[ExecutionStatus, int, int, list, Memory]:
        """
        Execute the program blob `p` as per Psi specification.

        Args:
            program: Program context / Cached for faster execution
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
        remaining_gas = gas

        logger.debug(
            "Starting PVM execution",
            registers=registers,
            inst_size=len(program.instruction_set),
            initial_pc=program_counter,
            initial_gas=gas,
            program_size=len(program.zeta),
        )

        while True:
            try:
                opcode = program.zeta[program_counter]

                status, program_counter, registers, memory = (
                    inst_map.execute_instruction(
                        opcode, program, program_counter, registers, memory
                    )
                )

                gas_cost = inst_map.get_gas_cost(opcode)
                remaining_gas -= gas_cost

                if remaining_gas < 0:
                    logger.warning(
                        "PVM - OUT_OF_GAS",
                        final_pc=program_counter,
                        gas_deficit=abs(remaining_gas),
                    )
                    status = OUT_OF_GAS
                    break

                elif status == ExecutionStatus.HALT:
                    logger.info(
                        "PVM - HALT",
                        final_pc=program_counter,
                        gas_remaining=remaining_gas,
                    )
                    break
                elif status == ExecutionStatus.HOST:
                    logger.debug(
                        "PVM - HOST", pc=program_counter, gas_remaining=remaining_gas
                    )
                    break

            except PvmError as e:
                logger.error(
                    "PVM execution error",
                    error_message=str(e),
                    error_code=e.code,
                    pc=program_counter,
                    gas_remaining=remaining_gas,
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
                    pc=program_counter,
                )
                raise e

        logger.info(
            "PVM result",
            final_pc=program_counter,
            gas_remaining=remaining_gas,
            registers=registers,
            memory=memory,
        )

        return status, program_counter, remaining_gas, registers, memory
