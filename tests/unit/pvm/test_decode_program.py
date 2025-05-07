import os
import json
from .types import Status, Testcase


def test_decode_program():
    # Read all json files from /data/pvm/programs
    data_dir = "tests/unit/pvm/data"
    for i, file in enumerate(os.listdir(data_dir)):
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            testcase = Testcase.from_json(data)

            assert testcase.initial_regs is not None
            assert testcase.initial_pc is not None
            assert testcase.initial_memory is not None
            assert testcase.program is not None
            assert testcase.expected_status is not None
            assert testcase.expected_regs is not None

            assert len(testcase.initial_regs) == len(data["initial-regs"])
            assert testcase.initial_pc == data["initial-pc"]
            assert len(testcase.initial_memory) == len(data["initial-memory"])
            assert len(testcase.program.jump_table) == data["program"][0]
            assert testcase.program.z == data["program"][1]
            assert testcase.expected_status == Status.from_json(data["expected-status"])
            assert len(testcase.expected_regs) == len(data["expected-regs"])
            assert testcase.expected_pc == data["expected-pc"]
            assert len(testcase.expected_memory) == len(data["expected-memory"])
            assert testcase.expected_gas == data["expected-gas"]
