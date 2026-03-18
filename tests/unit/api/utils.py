"""
Test utilities for RPC tests.

Loads extracted vector blocks and imports them via state transition.
Provides b64 helpers for comparing RPC responses.
"""
import json
import base64
from pathlib import Path
from dataclasses import dataclass

from jam.block.block import Block
from jam.types.protocol.crypto import HeaderHash


VECTORS_DIR = Path(__file__).parents[2] / "chain"


def load_test_blocks():
    with open(VECTORS_DIR / "test_blocks.json") as f:
        return json.load(f)


def load_test_services():
    with open(VECTORS_DIR / "test_service.json") as f:
        return json.load(f)


def load_test_packages():
    with open(VECTORS_DIR / "test_packages.json") as f:
        return json.load(f)


# ─── b64 helpers ───

def b64e(val) -> str:
    """Encode to base64 string. Accepts hex string, bytes, or Codable."""
    if isinstance(val, str):
        val = bytes.fromhex(val)
    elif hasattr(val, "encode") and callable(val.encode):
        val = val.encode()
    return base64.b64encode(val).decode("ascii")


def b64d(val: str) -> bytes:
    """Decode base64 string to bytes."""
    return base64.b64decode(val)


def b64_hex(val: str) -> str:
    """Decode base64 string to hex."""
    return base64.b64decode(val).hex()


# ─── Chain import ───

@dataclass
class ImportedBlock:
    index: int
    slot: int
    block: Block
    header_hash: str       # hex
    pre_state_root: str    # hex
    post_state_root: str   # hex
    raw: dict
    success: bool = False

    @property
    def header_hash_b64(self) -> str:
        """header_hash as b64 — matches what RPC returns."""
        return b64e(self.header_hash)

    @property
    def post_state_root_b64(self) -> str:
        return b64e(self.post_state_root)


def import_chain(node, up_to=None, finalize_to=None):
    """Import vector blocks through full state transition.

    Args:
        node: JamNode instance
        up_to: Import blocks up to this index (inclusive). None = all.
        finalize_to: Finalize blocks up to this index (inclusive).
            None = finalize all (instant_finality=True for every block).
            Set to e.g. 3 to finalize blocks 1-3 and only stash blocks 4+.

    Finalized blocks go through: save → stash → finalize → settle.
    Non-finalized blocks go through: save → stash only.
    """
    test_blocks = load_test_blocks()

    if up_to is None:
        up_to = len(test_blocks)
    if finalize_to is None:
        finalize_to = up_to

    results = []
    for bv in test_blocks:
        if bv["index"] > up_to:
            break

        block = Block.from_json(bv["block"])
        finalize = bv["index"] <= finalize_to
        success = node.state._force_transition(block, instant_finality=finalize, skip_hooks=True)
        if finalize:
            print("FINALIZING BLock", bv["index"], finalize_to, bv["header_hash"])
        results.append(ImportedBlock(
            index=bv["index"],
            slot=bv["slot"],
            block=block,
            header_hash=bv["header_hash"],
            pre_state_root=bv["pre_state_root"],
            post_state_root=bv["post_state_root"],
            raw=bv,
            success=success,
        ))

    return results


def finalize_block(node, ib: ImportedBlock):
    """Manually finalize a stashed (non-finalized) block.

    Mirrors what instant_finality=True does inside transition():
    mark_as_audited → finalise → settle.

    State must be loaded BEFORE advancing finality, otherwise load_cache
    finds target == finalized and traverses zero records.
    """
    from jam.state.state import State
    hh = HeaderHash.fromhex(ib.header_hash)

    # Load state while finalized head is still the previous block
    state = State.load(node, hh)
    state.store.enable_writes()

    # Now advance finality
    node.ledger.mark_as_audited(ib.block)
    node.grandpa.finalise(ib.block, initial=True)

    # Settle the loaded state into the node
    state.settle(hh)


async def rpc_call(node, method, params=None):
    """Make a JSON-RPC call. Returns (status_code, parsed_json).

    Params should be b64 strings for byte-like values (header hashes etc).
    Response values are b64 strings for byte fields, plain ints for int fields.
    """
    async with node.responder.app.test_client() as client:
        resp = await client.post("/", json={
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 3,
        })
        data = await resp.get_json()
        return resp.status_code, data
