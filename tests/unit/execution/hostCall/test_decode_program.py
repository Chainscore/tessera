# import os
# import json
# from .types import TestCases


# def test_decode_program():
#     # Read all json files from /data/pvm/programs
#     data_dir = "tests/unit/hostCall/data"
#     for root, _, files in os.walk(data_dir):
#         for file in files:
#             if file.endswith(".json"):  # Process only JSON files
#                 file_path = os.path.join(root, file)

#                 # Read and clean the JSON file
#                 with open(file_path, "r") as f:
#                     data = json.load(f)  # `json.load(f)` is better than `json.loads(f.read())`
#                     cleaned_data = remove_none_values(data)

#                 # Write back the cleaned data
#                 with open(file_path, "w") as f:
#                     json.dump(cleaned_data, f, indent=4)
#                     print(f"Cleaned: {file_path}")

#                 # Convert to TestCases object
#                 testcase = TestCases.from_json(cleaned_data)
#                 assert testcase.initial_regs is not None
#                 assert testcase.initial_memory is not None
#                 assert testcase.initial_memory is not None
#                 assert testcase.initial_gas is not None
#                 assert testcase.expected_regs is not None

#             # print(testcase)
#             # assert testcase.initial_regs == data["initial-regs"]
#             # assert testcase.initial_memory == data["initial-memory"]
#             # assert testcase.initial_gas == data["initial-gas"]
#             # assert testcase.initial_service_account == data.get("initial-service-account", {})
#             # assert testcase.initial_service_index == data.get("initial-service-index", None)
#             # assert testcase.initial_delta == data.get("initial-delta", {})
#             # assert testcase.initial_xcontent_x == data.get("initial-xcontent-x", {})
#             # assert testcase.initial_xcontent_y == data.get("initial-xcontent-y", {})
#             # assert testcase.initial_refine_map == data.get("initial-refine-map", {})
#             # assert testcase.initial_export_segment == data.get("initial-export-segment", [])
#             # assert testcase.initial_export_segment_index == data.get("initial-export-segment-index", None)
#             # assert testcase.initial_timeslot == data.get("initial-timeslot", None)
#             # assert testcase.expected_regs == data["expected-regs"]
#             # assert testcase.expected_memory == data["expected-memory"]
#             # assert testcase.expected_gas == data["expected-gas"]
#             # assert testcase.expected_service_account == data.get("expected-service-account", {})
#             # assert testcase.expected_delta == data.get("expected-delta", {})
#             # assert testcase.expected_xcontent_x == data.get("expected-xcontent-x", {})
#             # assert testcase.expected_xcontent_y == data.get("expected-xcontent-y", {})
#             # assert testcase.expected_refine_map == data.get("expected-refine-map", {})
#             # assert testcase.expected_export_segment == data.get("expected-export-segment", [])


# def remove_none_values(data):
#     if isinstance(data, dict):
#         return {k: remove_none_values(v) for k, v in data.items() if v is not None}
#     elif isinstance(data, list):
#         return [remove_none_values(item) for item in data]
#     else:
#         return data


# def process_json_file(input_file, output_file):
#     with open(input_file, 'r') as f:
#         data = json.load(f)

#     cleaned_data = remove_none_values(data)

#     with open(output_file, 'w') as f:
#         json.dump(cleaned_data, f, indent=4)

#     return cleaned_data
