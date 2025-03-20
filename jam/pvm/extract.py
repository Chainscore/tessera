import copy
from jam.pvm.opcode_mapping import InstructionMapper
from jam.pvm.register import Registers
from jam.types.base.integers.fixed import U32
from jam.pvm.pvm_memory import PageMemory
from jam.types.base.enum import Enum


class Status(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"


class Execution:
    def __init__(self,
                 initial_registers: Registers,
                 gas: U32,
                 memory: PageMemory,
                 pc: U32,
                 program):
        self.initial_regs = initial_registers
        self.initial_pc = pc
        self.initial_memory = memory
        self.initial_gas = gas
        self.program = program
        self.status: Status = Status('panic')

    @staticmethod
    def skip(k, i):
        for j in range(i + 1, len(k)):
            if k[j] == 1:
                return j - i  # Distance to the next opcode.
        return len(k) - i  # Reached the end of the bitmask.

    def process_program(self):
        i = self.initial_pc
        while i < len(self.program.instruction_set):
            self.initial_pc = i
            if i >= len(self.program.offset_bitmask):
                break
            if self.program.offset_bitmask[i]:
                pc = int(copy.deepcopy(i))
                index = Execution.skip(self.program.offset_bitmask, pc)
                instruction_subset = self.program.instruction_set[i+1: i + index]
                group, function = InstructionMapper.get_instruction(self.program.instruction_set[i].value)
                branch_i = InstructionMapper.execute(self.program.instruction_set[i].value, self, instruction_subset)
                if branch_i == "panic" or branch_i == "page-fault" or branch_i == "halt":
                    self.status = Status(branch_i)
                    return self
                if isinstance(branch_i, int):  # Check if branch_i is an integer
                    if group == "reg_imm" or group == "reg_reg_imm_imm":
                        i = branch_i
                    else:
                        if branch_i == 0:
                            i += 1
                        i += branch_i  # Modify i only if branch_i is an integer
                else:
                    i += index
                    continue  # Continue execution regardless
            else:
                # Move to the next offset if the current bitmask is not set
                i += 1
        # print(self.initial_memory, self.initial_pc)
        return self
