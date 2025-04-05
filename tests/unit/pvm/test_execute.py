import os
import json
from .types import Testcase

def get_testcases_starting_with(prefix: str):
    data_dir = "tests/unit/pvm/data"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield Testcase.from_json(data)

def test_inst_add_32():
    # Read all json files from /data/pvm/programs
    for tc in get_testcases_starting_with("inst_store_imm_indirect_u8_with_offset_ok"):
        print("Testcase name: ", tc.name)
        status, pc, gas, registers, memory = tc.program.execute(
            tc.initial_pc,
            tc.initial_gas,
            tc.initial_regs,
            tc.initial_memory.to_memory(tc.initial_page_map),
        )
        assert registers == tc.expected_regs
        assert memory == tc.expected_memory.to_memory(tc.initial_page_map)
        assert pc == tc.expected_pc
        assert status.code == tc.expected_status