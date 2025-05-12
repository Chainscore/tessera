import os
import json
from pathlib import Path

import pytest

from jam.execution.host_calls.invocations.functions.refine_fns import RefineFunctions
from .types import TestCases

TEST_DATA_DIR = Path("tests/unit/hostCall/data/")

def get_testcases_starting_with(prefix: str):
    data_dir = "historical_lookup"
    for i, file in enumerate(os.listdir(data_dir)):
        if file.startswith(prefix):
            print(f"Reading file, now reading riscv test cases which are too large to debug: {file}")
            with open(os.path.join(data_dir, file), "r") as f:
                data = json.loads(f.read())
                yield TestCases.from_json(data)


class TestHostCalls:
    @pytest.mark.parametrize("test_file", TEST_DATA_DIR.glob("hist*/*.json"))
    def test_host_call(self, test_file: Path):
        with open(test_file, "r") as f:
            vector = json.load(f)
            print(f"\nTesting {vector['name']} ...")
            print(vector)
