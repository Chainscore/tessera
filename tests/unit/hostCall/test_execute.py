import os
import json
from .types import TestCases
from jam.hostCall.transition import HostTransition


def get_testcases_starting_with(prefix: str):
    data_dir = "tests/unit/hostCall/data/poke"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            print(f"Reading file, now reading riscv test cases which are too large to debug: {file}")
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield TestCases.from_json(data)


def test_host_call():
    # Read all json files from /data/pvm/programs
    for tc in get_testcases_starting_with(""):
        print(tc)
        regs, memory, service, delta, xcontent, refine_map = HostTransition.transit(tc)
        print(regs, memory, service, delta, xcontent, refine_map)
        # TODO: Uncomment this when we have implemented Host calls

        # assert output.initial_regs == tc.expected_regs
        # assert output.initial_pc == tc.expected_pc
        # assert output.initial_memory == tc.expected_memory
        # assert output.status == tc.expected_status

        continue
