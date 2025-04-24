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
    assert pc == tc.expected_pc
    assert registers == tc.expected_regs
    assert memory == tc.expected_memory.to_memory(tc.initial_page_map)
    assert status.code == tc.expected_status

# def test_inst_jump():
#     print("\n\n-------------------------- inst_jump --------------------------")
#     for tc in get_testcases_starting_with("inst_jump"):
#         vector_run(tc)

# def test_inst_add():
#     print("\n\n-------------------------- inst_add --------------------------")
#     for tc in get_testcases_starting_with("inst_add"):
#         vector_run(tc)

# def test_inst_branch():
#     print("\n\n-------------------------- inst_branch --------------------------")
#     for tc in get_testcases_starting_with("inst_branch"):
#         vector_run(tc)

# def test_inst_div():
#     print("\n\n-------------------------- inst_div --------------------------")
#     for tc in get_testcases_starting_with("inst_div"):
#         vector_run(tc)

# def test_inst_mul():
#     print("\n\n-------------------------- inst_mul --------------------------")
#     for tc in get_testcases_starting_with("inst_mul"):
#         vector_run(tc)

# def test_inst_load():
#     print("\n\n-------------------------- inst_load --------------------------")
#     for tc in get_testcases_starting_with("inst_load"):
#         vector_run(tc)

# def test_inst_rem():
#     print("\n\n-------------------------- inst_rem --------------------------")
#     for tc in get_testcases_starting_with("inst_rem"):
#         vector_run(tc)

# def test_inst_shift():
#     print("\n\n-------------------------- inst_shift --------------------------")
#     for tc in get_testcases_starting_with("inst_shift"):
#         vector_run(tc)

# def test_inst_rem():
#     print("\n\n-------------------------- inst_rem --------------------------")
#     for tc in get_testcases_starting_with("inst_rem"):
#         vector_run(tc)

# def test_inst_store():
#     print("\n\n-------------------------- inst_store --------------------------")
#     for tc in get_testcases_starting_with("inst_store"):
#         vector_run(tc)

# def test_inst_sub():
#     print("\n\n-------------------------- inst_sub --------------------------")
#     for tc in get_testcases_starting_with("inst_sub"):
#         vector_run(tc)

# def test_inst():
#     print("\n\n-------------------------- inst --------------------------")
#     for tc in get_testcases_starting_with("inst"):
#         vector_run(tc)

# def test_riscv():
#     print("\n\n-------------------------- inst --------------------------")
#     for tc in get_testcases_starting_with("riscv"):
#         vector_run(tc)