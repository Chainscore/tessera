import json
import os
from jam.pvm.program import Program
from jam.pvm.opcode_mapping import InstructionMapper


class Execution:
    def __init__(self, data):
        self.initial_regs = data["initial-regs"]
        self.initial_pc = data["initial-pc"]
        self.initial_page_map = data["initial-page-map"]
        self.initial_memory = data["initial-memory"]
        self.initial_gas = data["initial-gas"]
        self.expected_regs = data["expected-regs"]
        self.expected_pc = data["expected-pc"]
        self.expected_memory = data["expected-memory"]
        self.expected_gas = data["expected-gas"]
        self.program = Program.from_json(bytes(data["program"]))

    @staticmethod
    def skip(k, i):
        """
        Calculate the number of bytes to skip to the next instruction's opcode.
        :param k: The opcode bitmask (list of 0s and 1s).
        :param i: The current index in the instruction data.
        :return: Number of bytes to skip.
        """
        for j in range(i + 1, len(k)):
            if k[j] == 1:
                return j - i  # Distance to the next opcode.
        return len(k) - i  # Reached the end of the bitmask.

    def process_program(self):
        opcode_value = "Unknown"
        i = 0
        while i < len(self.program.instruction_set):
            if self.program.offset_bitmask[i]:
                index = Execution.skip(self.program.offset_bitmask, i)

                # Collect the sub-array of instructions
                instruction_subset = self.program.instruction_set[i+1: i + index + 1]
                group, function = InstructionMapper.get_instruction(self.program.instruction_set[i].value)
                # print(group)
                InstructionMapper.execute(self.program.instruction_set[i].value, self, instruction_subset)
                if self.initial_regs == self.expected_regs:
                    print("test case passed")
                else:
                    print(f"initial regs:{self.initial_regs}")
                    print(f"expected regs:{self.expected_regs}")
                # Jump to i + index
                i += index
            else:
                # Move to the next element if the current bitmask is not set
                i += 1


def extract():
    folder_path = "../../tests/unit/pvm/data"

    # Get a list of all files in the folder
    all_files = sorted(os.listdir(folder_path))  # Sort to maintain consistent order

    # Filter files from index 1 to 12 (2nd to 13th files)
    selected_files = all_files[70:75]
    for file_name in selected_files:
        full_path = os.path.join(folder_path, file_name)
        with open(full_path, "r") as f:
            data = json.loads(f.read())

            # Create an instance of PVMProgram and process it
            program_obj = Execution(data)
            program_obj.process_program()


extract()
