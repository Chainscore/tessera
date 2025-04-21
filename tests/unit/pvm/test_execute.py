import os
import json

from jam.pvm.pvm import PVM
from .types import Testcase

def get_testcases_starting_with(prefix: str):
    data_dir = "tests/unit/pvm/data"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield Testcase.from_json(data)

def vector_run(tc: Testcase):
    print("\nProcessing test case: ", tc.name)
    status, pc, gas, registers, memory = PVM.execute(
        bytes(tc.program),
        tc.initial_pc,
        tc.initial_gas,
        tc.initial_regs,
        tc.initial_memory.to_memory(tc.initial_page_map),
    )
    assert registers == tc.expected_regs
    assert memory == tc.expected_memory.to_memory(tc.initial_page_map)
    assert pc == tc.expected_pc
    assert status.code == tc.expected_status

def test_inst_i_imm():
    # Read all json files from /data/pvm/programs
    for tc in get_testcases_starting_with("inst_jump."):
        vector_run(tc)
