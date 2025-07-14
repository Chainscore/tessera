import json
import random
import os

def main():
    # Dynamically locate the file relative to this script
    base_path = os.path.dirname(__file__)
    file_name = 'dummy_wp.json'
    file_path = os.path.join(base_path, file_name)

    # Check and print path before opening
    print(f"Looking for file at: {file_path}")

    if not os.path.exists(file_path):
        print(f"❌ File not found at: {file_path}")
        return

    # Load JSON and handle double-list structure
    with open(file_path, 'r') as f:
        raw_data = json.load(f)

    # Flatten if it's [[...]]
    if isinstance(raw_data, list) and isinstance(raw_data[0], list):
        data = raw_data[0]
    else:
        data = raw_data

    print(f"✅ Loaded {len(data)} entries from {file_name}")

    # Assign new random core_index from 0 to 334
    for entry in data:
        new_index = random.randint(0, 334)
        entry["core_index"] = new_index
        if "work_rep" in entry and "core_index" in entry["work_rep"]:
            entry["work_rep"]["core_index"] = new_index

    # Save updated data, preserving [[...]] wrapping if needed
    output_path = os.path.join(base_path, 'dummy_wr_updated.json')
    with open(output_path, 'w') as f:
        json.dump([data], f, indent=2)

    print(f"✅ Updated core_index values saved to: {output_path}")

if __name__ == "__main__":
    main()
