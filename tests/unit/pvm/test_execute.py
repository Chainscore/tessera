import os
import json
from pathlib import Path

import pytest

from jam.pvm.pvm import PVM
from .types import Testcase

TEST_DATA_DIR = Path("tests/unit/pvm")
PVM_DIR = TEST_DATA_DIR / "data"

def load_test_vectors(file_path: Path):
    """
    Load test vectors from a JSON file.

    Args:
        file_path: Path to test vector file

    Returns:
        List of test vectors

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, "r") as f:
        return json.loads(f.read())

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
    assert status.code == tc.expected_status
    assert registers == tc.expected_regs
    assert memory == tc.expected_memory.to_memory(tc.initial_page_map)

class TestInst:
    @pytest.mark.parametrize("test_file", PVM_DIR.glob("inst_store*.json"))
    def test_store(self, test_file: Path):
        vector_run(Testcase.from_json(load_test_vectors(test_file)))

    @pytest.mark.parametrize("test_file", PVM_DIR.glob("inst_load*.json"))
    def test_load(self, test_file: Path):
        vector_run(Testcase.from_json(load_test_vectors(test_file)))

    @pytest.mark.parametrize("test_file", PVM_DIR.glob("inst*.json"))
    def test_inst(self, test_file: Path):
        vector_run(Testcase.from_json(load_test_vectors(test_file)))

class TestRiscV:
    @pytest.mark.parametrize("test_file", PVM_DIR.glob("riscv*.json"))
    def test_riscv(self, test_file: Path):
        vector_run(Testcase.from_json(load_test_vectors(test_file)))