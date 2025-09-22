"""
JAM Test Vector Importer
"""
import json
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

from jam.block.block import Block
from tsrkit_types import Bytes


def load_test_vector(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)


def get_test_vector_files(import_path: str) -> List[str]:
    path = Path(import_path)
    
    if path.is_file():
        if path.suffix.lower() == '.json':
            return [str(path)]
        raise ValueError(f"Must be JSON file: {import_path}")
    
    elif path.is_dir():
        json_files = [str(f) for f in path.glob("*.json")]
        json_files.sort()
        return json_files
    
    raise ValueError(f"Path not found: {import_path}")


def setup_state_from_keyvals(state_db, keyvals: List[Dict[str, str]]):
    from jam.state.state import setup_state
    
    state_dict = {}
    for kv in keyvals:
        key = Bytes.from_json(kv["key"])
        value = Bytes.from_json(kv["value"])
        state_dict[key] = value
    
    return setup_state(state_db, state_dict)


def process_test_vector(test_vector: Dict[str, Any], state, settings) -> Tuple[Any, float]:
    pre_state = test_vector.get("pre_state", {})
    expected_pre_root = pre_state.get("state_root", "0x" + "00" * 32)
    if expected_pre_root.startswith("0x"):
        expected_pre_root = expected_pre_root[2:]
    
    # Update state only if root doesn't match
    if state.root.hex() != expected_pre_root:
        keyvals = pre_state.get("keyvals", [])
        if keyvals:
            state = setup_state_from_keyvals(settings.state_db, keyvals)
    
    # Process block if present
    transition_time = 0.0
    block_data = test_vector.get("block")
    if block_data:
        block = Block.from_json(block_data)
        start_time = time.time()
        state.transition(block)
        transition_time = time.time() - start_time
    
    return state, transition_time


async def run_import(db_path: str, import_path: str) -> None:
    print(f"Importing from: {import_path}")
    
    # Setup
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
    
    from jam.settings import setup_setting
    settings = setup_setting(db_path, 1, "importer", 40001)
    
    # Get files
    test_files = get_test_vector_files(import_path)
    if not test_files:
        print("No JSON files found")
        return
    
    print(f"Found {len(test_files)} test vector(s)")
    
    state = None
    processed = 0
    errors = 0
    transition_data = []  # Store (filename, time) pairs
    
    # Process each file
    for file_path in test_files:
        try:
            test_vector = load_test_vector(file_path)
            
            # Initialize state on first vector
            if state is None:
                pre_state = test_vector.get("pre_state", {})
                keyvals = pre_state.get("keyvals", [])
                import multiprocessing as mp
                state = setup_state_from_keyvals(settings.state_db, keyvals)
                print("start method after setup:", mp.get_start_method())

            # Process vector
            state, transition_time = process_test_vector(test_vector, state, settings)
            processed += 1
            
            filename = os.path.basename(file_path)
            if transition_time > 0:
                transition_data.append((filename, transition_time))

            post_root = test_vector.get("post_state", {}).get("state_root")
            if post_root:
                assert state.root.hex() == post_root[2:] if post_root.startswith("0x") else post_root, \
                f"State root mismatch after processing {filename}"
            
        except Exception as e:
            print(f"✗ {os.path.basename(file_path)}: {e}")
            errors += 1
    
    # Show timing table
    if transition_data:
        print(f"\n⏱️  State Transition Times:")
        print("File".ljust(40) + "Time (ms)")
        print("-" * 55)
        
        total_time = 0
        for filename, time_seconds in transition_data:
            time_ms = time_seconds * 1000
            total_time += time_seconds
            print(f"{filename:<40} {time_ms:>8.2f}")
        
        avg_time = total_time / len(transition_data)
        print("-" * 55)
        print(f"{'Average':<40} {(avg_time * 1000):>8.2f}")
        print(f"{'Total':<40} {(total_time * 1000):>8.2f}")
    
    print(f"\nDone: {processed} processed, {errors} errors")
