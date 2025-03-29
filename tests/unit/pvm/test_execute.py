import os
import json
from .types import Testcase
from jam.pvm.transition import PvmTransition
from jam.pvm.page_map import PageMap
from jam.pvm.pvm_memory import Memory, Access
from jam.types.base.boolean import Boolean
from jam.types.base.sequences.bytes.bytes import Bytes, Byte


def get_testcases_starting_with(prefix: str):
    data_dir = r"C:\Users\FAIZ AHMAD\PycharmProjects\jam-node\tests\unit\pvm\data"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            print(f"Reading file, now reading riscv test cases which are too large to debug:{file}")  # Print the filename
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield Testcase.from_json(data)


def test_inst_add_32():
    # Read all json files from /data/pvm/programs
    for tc in get_testcases_starting_with("inst_load"):
        # TODO: Uncomment this when we have implemented execute
        temp = PvmTransition.transit(tc.initial_memory, tc.initial_page_map)
        print(temp)
        page = PageMap()
        temp2 = PvmTransition.transit(tc.expected_memory, page, False)
        output = tc.program.execute(
            tc.initial_regs,
            tc.initial_gas,
            temp,
            tc.initial_pc,
        )
        assert output.initial_regs == tc.expected_regs
        assert output.initial_pc == tc.expected_pc
        assert all(
            (page1.value == temp2.pages[addr].value) if addr in temp2.pages and temp2.pages[addr].value
            else all(byte == Byte(0) for byte in page1.value)
            for addr, page1 in output.initial_memory.pages.items()
        )
        assert output.status == tc.expected_status

        continue
