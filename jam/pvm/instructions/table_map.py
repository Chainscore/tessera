from typing import List, Type
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.tables.i_reg_i_imm import InstructionsWArgs1Imm1Imm
from jam.types.base.integers.fixed import U8
from jam.pvm.instructions.instruction_table import InstructionTable

class InstTableMap:
    from jam.pvm.instructions.tables.i_imm import InstructionsWArgs1Imm
    from jam.pvm.instructions.tables.i_offset import WArgsOneOffset
    from jam.pvm.instructions.tables.i_reg_i_ewimm import InstructionsWArgs1Imm1EwImm
    from jam.pvm.instructions.tables.ii_imm import InstructionsWArgs2Imm
    from jam.pvm.instructions.tables.wo_args import InstructionsWoArgs

    # Mapping of opcodes to instruction tables
    # Key denotes the last opcode of the corresponding table
    ALL_INSTRUCTION_TABLES = {
        10: InstructionsWoArgs,
        20: InstructionsWArgs1Imm,
        30: InstructionsWArgs1Imm1EwImm,
        40: InstructionsWArgs2Imm,
        50: WArgsOneOffset,
        60: InstructionsWArgs1Imm1Imm
    }

    @classmethod
    def get_instructions_table(cls, opcode: U8) -> Type[InstructionTable]:
        """Opcode could be any integer, but it must be a valid opcode."""
        for key, value in cls.ALL_INSTRUCTION_TABLES.items():
            if opcode < key:
                return value
        raise PvmError(PvmErrorCodes.INVALID_OPCODE)

    @classmethod
    def terminating_blocks(cls) -> List[int]:
        """
        The terminating blocks are the blocks that will cause the execution to halt.
        To find out, iterate over the instruction tables and check if the opcode.is_terminating is True.
        """
        terminating_blocks = []
        for instruction_table in cls.ALL_INSTRUCTION_TABLES.values():
            for opc_id, opcode in instruction_table.table().items():
                if opcode.is_terminating:
                    terminating_blocks.append(opc_id)
        return terminating_blocks