import os
import json

from jam.types.protocol.core import Register
from .types import Testcase


def get_testcases_starting_with(prefix: str):
    data_dir = r"C:\Users\FAIZ AHMAD\PycharmProjects\jam-node\tests\unit\pvm\data"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            print(f"Reading file, now reading riscv test cases which are too large to debug: {file}")  # Print the filename
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield Testcase.from_json(data)


def test_inst_add_32():
    # Read all json files from /data/pvm/programs
    for tc in get_testcases_starting_with(""):
        # TODO: Uncomment this when we have implemented execute
        output = tc.program.execute(
            tc.initial_regs,
            tc.initial_gas,
            tc.initial_memory,
            tc.initial_pc,
            tc.initial_page_map
        )
        assert output.initial_regs == tc.expected_regs
        assert output.initial_pc == tc.expected_pc
        assert output.initial_memory == tc.expected_memory
        assert output.status == tc.expected_status

        continue
