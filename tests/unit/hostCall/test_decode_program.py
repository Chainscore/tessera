import os
import json
from .types import TestCases


def test_decode_program():
    # Read all json files from /data/pvm/programs
    data_dir = r"C:\Users\FAIZ AHMAD\PycharmProjects\jam-node\tests\unit\hostCall\data\upgrade"
    for i, file in enumerate(os.listdir(data_dir)):
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            print(data)
            testcase = TestCases.from_json(data)

            assert testcase.initial_regs is not None
            assert testcase.initial_memory is not None
            assert testcase.initial_memory is not None
            assert testcase.initial_gas is not None
            assert testcase.expected_regs is not None
            print(testcase)
            # assert testcase.initial_regs == data["initial-regs"]
            # assert testcase.initial_memory == data["initial-memory"]
            # assert testcase.initial_gas == data["initial-gas"]
            # assert testcase.initial_service_account == data.get("initial-service-account", {})
            # assert testcase.initial_service_index == data.get("initial-service-index", None)
            # assert testcase.initial_delta == data.get("initial-delta", {})
            # assert testcase.initial_xcontent_x == data.get("initial-xcontent-x", {})
            # assert testcase.initial_xcontent_y == data.get("initial-xcontent-y", {})
            # assert testcase.initial_refine_map == data.get("initial-refine-map", {})
            # assert testcase.initial_export_segment == data.get("initial-export-segment", [])
            # assert testcase.initial_export_segment_index == data.get("initial-export-segment-index", None)
            # assert testcase.initial_timeslot == data.get("initial-timeslot", None)
            # assert testcase.expected_regs == data["expected-regs"]
            # assert testcase.expected_memory == data["expected-memory"]
            # assert testcase.expected_gas == data["expected-gas"]
            # assert testcase.expected_service_account == data.get("expected-service-account", {})
            # assert testcase.expected_delta == data.get("expected-delta", {})
            # assert testcase.expected_xcontent_x == data.get("expected-xcontent-x", {})
            # assert testcase.expected_xcontent_y == data.get("expected-xcontent-y", {})
            # assert testcase.expected_refine_map == data.get("expected-refine-map", {})
            # assert testcase.expected_export_segment == data.get("expected-export-segment", [])
