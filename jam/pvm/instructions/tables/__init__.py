from jam.pvm.instructions.tables.i_imm import InstructionsWArgs1Imm
from jam.pvm.instructions.tables.i_offset import WArgsOneOffset
from jam.pvm.instructions.tables.i_reg_i_ewimm import InstructionsWArgs1Imm1EwImm
from jam.pvm.instructions.tables.i_reg_i_imm import InstructionsWArgs1Reg1Imm
from jam.pvm.instructions.tables.i_reg_ii_imm import InstructionsWArgs1Reg2Imm
from jam.pvm.instructions.tables.i_reg_i_imm_i_offset import InstructionsWArgs1Reg1Imm1Offset
from jam.pvm.instructions.tables.ii_imm import InstructionsWArgs2Imm
from jam.pvm.instructions.tables.ii_reg import InstructionsWArgs2Reg
from jam.pvm.instructions.tables.ii_reg_i_imm import InstructionsWArgs2Reg1Imm
from jam.pvm.instructions.tables.ii_reg_i_offset import InstructionsWArgs2Reg1Offset
from jam.pvm.instructions.tables.ii_reg_ii_imm import InstructionsWArgs2Reg2Imm
from jam.pvm.instructions.tables.iii_reg import InstructionsWArgs3Reg
from jam.pvm.instructions.tables.wo_args import InstructionsWoArgs

__all__ = [
    "InstructionsWArgs1Imm",
    "WArgsOneOffset",
    "InstructionsWArgs1Imm1EwImm",
    "InstructionsWArgs1Reg1Imm",
    "InstructionsWArgs1Reg2Imm",
    "InstructionsWArgs1Reg1Imm1Offset",
    "InstructionsWArgs2Imm",
    "InstructionsWArgs2Reg",
    "InstructionsWArgs2Reg1Imm",
    "InstructionsWArgs2Reg1Offset",
    "InstructionsWArgs2Reg2Imm",
    "InstructionsWArgs3Reg",
    "InstructionsWoArgs",
]