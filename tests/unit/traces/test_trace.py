"""
Simple trace test that runs on a single trace.json file.
"""
import json
import shutil
from pathlib import Path
from time import time
import pytest
from deepdiff import DeepDiff
from jam.settings import setup_setting
from jam.log_setup import setup_logging
from jam.state.state import setup_state
from rockstore import RockStore
from jam.block.block import Block
from tsrkit_types import Bytes


TRACE_FILE = Path(__file__).parent / "trace.json"


def load_trace():
    """Loads trace.json and returns pre_state, block, post_state, expected_root."""
    with open(TRACE_FILE, 'r') as f:
        data = json.load(f)

    pre_state = {
        Bytes.from_json(kv["key"]): Bytes.from_json(kv["value"]) 
        for kv in data["pre_state"]["keyvals"]
    }
    block = Block.from_json(data["block"])
    post_state = {
        Bytes.from_json(kv["key"]): Bytes.from_json(kv["value"]) 
        for kv in data["post_state"]["keyvals"]
    }
    expected_root = data["post_state"]["state_root"].replace("0x", "")

    return pre_state, block, post_state, expected_root

@pytest.mark.skip
@pytest.mark.asyncio
async def test_trace():
    """Test trace.json transition."""
    setup_logging(theme="gruvbox", node_name="test")
    
    # Load trace data
    pre_state, block, post_state, expected_root = load_trace()
    
    # Setup isolated environment
    work_dir = Path("data/tmp") / f"{int(time() * 1000000)}"
    setup_setting(data_path=str(work_dir / "main"), rpc_flag=False)
    
    db_main = RockStore(str(work_dir / "main"))
    db_post = RockStore(str(work_dir / "post"))

    try:
        # Setup Pre-State
        state = setup_state(db_main, pre_state)
        
        # Apply Transition
        state.transition(block, False, True)
        state.settle(block.header.hash())
        
        # Setup Expected Post-State (for comparison)
        expected_state = setup_state(db_post, post_state)
        
        # Check sub-roots (pi, rho, beta, gamma)
        for attr in ['pi', 'rho', 'beta', 'gamma']:
            actual_val = getattr(state, attr)
            expect_val = getattr(expected_state, attr)
            if actual_val != expect_val:
                print(f"\nCOMPONENT: {attr.upper()}")
                print("ACT\n", actual_val.to_json())
                print("EXP\n", expect_val.to_json())
                diff = DeepDiff(actual_val.to_json(), expect_val.to_json(),
                              significant_digits=0, verbose_level=2, view="tree")
                print(f"\n⚠️ Mismatched {attr.upper()}:\n{diff}")

        # Check key-value storage
        actual_kv = {k.hex(): v.hex() for k, v in state.store._DB.get_all().items()}
        expect_kv = {k.hex(): v.hex() for k, v in post_state.items()}

        val_diff = DeepDiff(actual_kv, expect_kv, significant_digits=0, verbose_level=2, view="tree")

        if val_diff:
            for k, v in expect_kv.items():
                if k not in actual_kv:
                    print(f"❌ Missing Key: {k}")
                elif actual_kv[k] != v:
                    print(f"❌ Value Diff [{k}]:\n   Exp: {v}\n   Act: {actual_kv[k]}")
            print("Storage Mismatch!")

        # Check State Merkle Root
        assert state.root.hex() == expected_root, \
            f"Root Mismatch!\nExpected: {expected_root}\nActual:   {state.root.hex()}"
        
        print("✅ Test Passed!")

    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)
