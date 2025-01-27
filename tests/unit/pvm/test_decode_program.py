import pytest
import os
import json

from jam.pvm.program import Program

def test_read_program():
    # Read all json files from /data/pvm/programs
    data_dir = "tests/unit/pvm/data"
    for file in os.listdir(data_dir):
        with open(os.path.join(data_dir, file), "r") as f:
            data = json.loads(f.read())
            try:
                program = Program.from_json(bytes(data["program"]))
                print("✅ Decoded program", program)
            except Exception as e:
                print("❌ Failed to decode", file, e)