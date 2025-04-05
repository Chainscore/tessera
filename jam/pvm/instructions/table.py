
from typing import List, Tuple
from jam.pvm.instructions.protocol import InstructionTable
from jam.pvm.instructions.tables.wo_args import InstructionsWoArgs
from jam.pvm.instructions.tables.i_imm import InstructionsWArgs1Imm
from jam.pvm.instructions.tables.ii_imm import InstructionsWArgs2Imm
from jam.pvm.instructions.tables.i_reg_i_ewimm import InstructionsWArgs1Imm1EwImm
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import ExecutionStatus
from jam.pvm.zeta import Zeta
from jam.types.base.integers.fixed import U8
from jam.types.protocol.core import Gas, RemainingGas

# Mapping of opcodes to instruction tables
# Key denotes the last opcode of the corresponding table
ALL_INSTRUCTION_TABLES = {
    10: InstructionsWoArgs,
    20: InstructionsWArgs1Imm,
    30: InstructionsWArgs1Imm1EwImm,
    40: InstructionsWArgs2Imm
}

def get_instructions_table(opcode: int) -> InstructionTable:
    """Opcode could be any integer, but it must be a valid opcode."""
    for key, value in ALL_INSTRUCTION_TABLES.items():
        if opcode < key:
            return value
    raise ValueError(f"Invalid opcode: {opcode}")


def terminating_blocks() -> List[int]:
    """
    The terminating blocks are the blocks that will cause the execution to halt.
    To find out, iterate over the instruction tables and check if the opcode.is_terminating is True.
    """
    terminating_blocks = []
    for instruction_table in ALL_INSTRUCTION_TABLES.values():
        for opc_id, opcode in instruction_table.table().items():
            if opcode.is_terminating:
                terminating_blocks.append(opc_id)
    return terminating_blocks

def execute(
        program_counter: U8,
        registers: Registers,
        memory: Memory,
        skip_index: U8,
        zeta: Zeta,
        gas: Gas
) -> Tuple[ExecutionStatus, U8, RemainingGas, Registers, Memory]:
    """
    Find and execute on the correct instruction table for the given opcode.

    Args:
        program_counter (U8): The program counter.
        initial_registers (Registers): Current registers.
        initial_memory (Memory): Current memory.
        skip_index (U8): The skip index.
        zeta (Zeta): The zeta.
        gas (Gas): The gas.

    Returns:
        Tuple[ExecutionStatus, U8, RemainingGas, Registers, Memory]: The execution status, the program counter, the remaining gas, the registers, and the memory.
    """
    opcode = zeta[program_counter]
    table = get_instructions_table(opcode)(zeta, skip_index, program_counter)
    status, registers, memory = table.execute(registers, memory)
    return status, program_counter + skip_index, gas, registers, memory