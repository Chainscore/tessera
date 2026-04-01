"""
JAM Test Vector Importer
"""
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, NamedTuple

from jam.block.block import Block
from jam.log_setup import logger
from jam.state.state import setup_state
from tsrkit_types import Bytes, structure, TypedVector


@structure
class KeyVal:
    key: Bytes[31]
    value: Bytes


@structure
class StateKeyVals:
    state_root: Bytes[32]
    keyvals: TypedVector[KeyVal]


@structure
class Trace:
    pre_state: StateKeyVals
    block: Block
    post_state: StateKeyVals

class TraceCase(NamedTuple):
    """Normalized trace test case data."""
    id: str  # e.g., "1766243315_8065_00000035"
    file_path: Path
    pre_state: Dict[bytes, bytes]
    pre_root: str
    block: Block
    post_state: Dict[bytes, bytes]
    expected_root: str  # Hex string without 0x

def load_test_vector(file_path: Path) -> TraceCase:
    trace = Trace.decode(file_path.read_bytes())
    case_id = f"{file_path.parent.name}_{file_path.stem}"

    case =  TraceCase(
        id=case_id,
        file_path=file_path,
        pre_state={item.key: item.value for item in trace.pre_state.keyvals},
        pre_root = trace.pre_state.state_root.hex(),
        block=trace.block,
        post_state={item.key: item.value for item in trace.post_state.keyvals},
        expected_root=trace.post_state.state_root.hex()
    )

    return case

def get_test_vector_files(import_path: str) -> List[Path]:
    path = Path(import_path)

    if path.is_file():
        if path.suffix.lower() == '.bin':
            return [path]
        raise ValueError(f"Must be BIN file: {import_path}")
    
    elif path.is_dir():
        files = [f for f in path.glob("*.bin")]
        # files.sort()
        return files
    
    raise ValueError(f"Path not found: {import_path}")


def process_test_vector(test_vector: TraceCase, state, settings) -> Tuple[Any, float]:
    pre_state = test_vector.pre_state
    expected_pre_root = test_vector.pre_root
    if expected_pre_root.startswith("0x"):
        expected_pre_root = expected_pre_root[2:]
    
    # Update state only if root doesn't match
    if state.root.hex() != expected_pre_root:
        logger.warning("Pre State doesn't match, recomputing Pre State")
        state = setup_state(settings.state_db, pre_state)
    
    # Process block if present
    transition_time = 0.0
    block = test_vector.block
    start_time = time.time()
    from jam.state.state import State
    is_valid = State._force_transition(block, False)
    if is_valid:
        state = State.load(block.header.hash())
    else:
        state = State.load(block.header.parent)
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
        print("No BIN files found")
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
                state = setup_state(settings.state_db, test_vector.pre_state)

            # Process vector
            state, transition_time = process_test_vector(test_vector, state, settings)
            processed += 1
            
            filename = os.path.basename(file_path)
            if transition_time > 0:
                transition_data.append((filename, transition_time))

            post_root = test_vector.expected_root
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
