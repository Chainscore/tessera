import os
import json

from jam.types.protocol.core import Register
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
    for tc in get_testcases_starting_with("inst_add_32"):
        # TODO: Uncomment this when we have implemented execute
        # output = tc.program.execute(
        #     Register(0),
        #     tc.initial_regs,
        #     tc.initial_memory,
        #     tc.initial_gas
        # )
        # assert output == tc.expected_regs
        continue