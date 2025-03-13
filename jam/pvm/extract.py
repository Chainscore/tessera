import copy
import json
import os
from jam.pvm.opcode_mapping import InstructionMapper
from jam.pvm.register import Registers
from jam.types.base.integers.fixed import U32
from jam.pvm.memory import MemoryChunk
from jam.pvm.page_map import PageMap
from jam.types.base.enum import Enum


class Status(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"


class Execution:
    def __init__(self,
                 initial_registers: Registers,
                 gas: U32,
                 memory: MemoryChunk,
                 pc: U32,
                 page_map: PageMap,
                 program):
        self.initial_regs = initial_registers
        self.initial_pc = pc
        self.initial_page_map = page_map
        self.initial_memory = memory
        self.initial_gas = gas
        self.program = program
        self.status: Status = Status('panic')
        # self.expected_regs = data["expected-regs"]
        # self.expected_pc = data["expected-pc"]
        # self.expected_memory = data["expected-memory"]
        # self.expected_gas = data["expected-gas"]

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
        return self


# function for testing, remove after integrating execution function with test.py
# def extract(prefix: str):
#     folder_path = "../../tests/unit/pvm/data"
#
#     # Get a sorted list of all files in the folder
#     all_files = sorted(os.listdir(folder_path))  # Sorting ensures consistent order
#     total_tests = 0
#     passed_tests = 0
#     # Filter files that start with the given prefix
#     selected_files = [file_name for file_name in all_files if file_name.startswith(prefix)]
#     for file_name in all_files:
#         full_path = os.path.join(folder_path, file_name)
#         if total_tests - passed_tests >= 1:
#             break
#         with open(full_path, "r") as f:
#             data = json.loads(f.read())
#             # Create an instance of Execution and process it
#             program_obj = Execution(data)
#             print(program_obj.initial_memory)
#             data = program_obj.process_program()
#             total_tests += 1
#             if data.initial_regs == data.expected_regs and data.initial_pc == data.expected_pc and data.initial_memory == data.expected_memory:
#                 print(f"✅✅✅✅✅ Test case PASSED: {file_name}")
#                 passed_tests += 1
#             else:
#                 print(f"❌❌❌❌❌ Test case FAILED: {file_name}")
#                 print(f"Initial_regs: {data.initial_regs} | Expected regs: {data.expected_regs}")
#                 print(f"Initial memory: {data.initial_memory} | Expected memory: {data.expected_memory}")
#                 print(f"Initial_pc: {data.initial_pc} | Expected pc: {data.expected_pc}")
#     print("\n==========================")
#     print(f"Total Test Cases: {total_tests}")
#     print(f"Passed Test Cases: {passed_tests}")
#     print(f"Failed Test Cases: {total_tests - passed_tests}")
#     print("==========================\n")
#
#
# # Example Usage:
# extract("inst_add")  # This will process all files starting with the given string
