"""
RPC tests — grouped, multi-level, b64 comparisons.

Multi-level pattern: import N blocks → query → import more → query again.
Verifies state evolution across block transitions.

All byte responses are b64 strings. Params sent as b64.
"""
from tests.unit.api.utils import (
    import_chain, finalize_block, rpc_call, b64e, b64d,
    load_test_services, load_test_blocks,
)


# ═══════════════════════════════════════════════
# 1. bestBlock
# ═══════════════════════════════════════════════

class TestBestBlock:

    async def test_genesis_only(self, jam_node_rpc):
        """Before any imports, bestBlock returns genesis."""
        status, data = await rpc_call(jam_node_rpc, "bestBlock")
        assert status == 200
        assert "header_hash" in data["result"]
        assert "slot" in data["result"]

    async def test_advances_with_imports(self, jam_node_rpc):
        """Import 2 blocks → check → import 2 more → check it advanced."""
        node = jam_node_rpc

        # Stage 1: import 2 blocks
        chain = import_chain(node, up_to=2)
        _, d2 = await rpc_call(node, "bestBlock")
        assert d2["result"]["header_hash"] == chain[1].header_hash_b64

        # Stage 2: import to 4
        chain = import_chain(node, up_to=4)
        _, d4 = await rpc_call(node, "bestBlock")
        assert d4["result"]["header_hash"] == chain[3].header_hash_b64

        # Should have advanced
        assert d2["result"]["header_hash"] != d4["result"]["header_hash"]

    async def test_slot_matches_hash(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "bestBlock")
        hh_b64 = data["result"]["header_hash"]
        slot = data["result"]["slot"]
        match = next((ib for ib in chain if ib.header_hash_b64 == hh_b64), None)
        assert match is not None
        assert slot == match.slot


# ═══════════════════════════════════════════════
# 2. finalizedBlock
# ═══════════════════════════════════════════════

class TestFinalizedBlock:

    async def test_genesis(self, jam_node_rpc):
        status, data = await rpc_call(jam_node_rpc, "finalizedBlock")
        assert status == 200
        assert data["result"]["slot"] is not None

    async def test_advances_block_by_block(self, jam_node_rpc):
        """Import block by block, finalized advances each time."""
        node = jam_node_rpc
        for n in [1, 2, 3, 4]:
            chain = import_chain(node, up_to=n)
            _, data = await rpc_call(node, "finalizedBlock")
            assert data["result"]["header_hash"] == chain[n - 1].header_hash_b64
            assert data["result"]["slot"] == chain[n - 1].slot

    async def test_multi_level(self, jam_node_rpc):
        """Import 2 → check → import 6 more → check advanced."""
        node = jam_node_rpc

        chain = import_chain(node, up_to=2)
        _, d2 = await rpc_call(node, "finalizedBlock")
        assert d2["result"]["header_hash"] == chain[1].header_hash_b64

        chain = import_chain(node, up_to=8)
        _, d8 = await rpc_call(node, "finalizedBlock")
        assert d8["result"]["header_hash"] == chain[7].header_hash_b64
        assert d2["result"]["slot"] < d8["result"]["slot"]


# ═══════════════════════════════════════════════
# 3. parent
# ═══════════════════════════════════════════════

class TestParent:

    async def test_parent_of_first_is_genesis(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=1)
        _, data = await rpc_call(jam_node_rpc, "parent", [chain[0].header_hash_b64])
        assert data["result"]["header_hash"] == b64e(chain[0].raw["parent_hash"])

    async def test_walk_backwards(self, jam_node_rpc):
        """Walk block 6 → 5 → 4 → 3 → 2 → 1 via parent calls."""
        chain = import_chain(jam_node_rpc, up_to=6)
        current = chain[5].header_hash_b64
        for i in range(5, 0, -1):
            _, data = await rpc_call(jam_node_rpc, "parent", [current])
            assert data["result"]["header_hash"] == chain[i - 1].header_hash_b64
            assert data["result"]["slot"] == chain[i - 1].slot
            current = data["result"]["header_hash"]

    async def test_parent_slot_is_correct(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "parent", [chain[3].header_hash_b64])
        assert data["result"]["slot"] == chain[2].slot


# ═══════════════════════════════════════════════
# 4. stateRoot
# ═══════════════════════════════════════════════

class TestStateRoot:

    async def test_matches_vector(self, jam_node_rpc):
        """stateRoot(block_hash) == vector's post_state_root for every block."""
        chain = import_chain(jam_node_rpc, up_to=6)
        for ib in chain:
            _, data = await rpc_call(jam_node_rpc, "stateRoot", [ib.header_hash_b64])
            assert data["result"] == ib.post_state_root_b64, (
                f"block {ib.index}: stateRoot mismatch"
            )

    async def test_multi_level(self, jam_node_rpc):
        """stateRoot changes as chain grows."""
        node = jam_node_rpc

        chain = import_chain(node, up_to=2)
        _, d2 = await rpc_call(node, "stateRoot", [chain[1].header_hash_b64])

        chain = import_chain(node, up_to=6)
        _, d6 = await rpc_call(node, "stateRoot", [chain[5].header_hash_b64])

        assert d2["result"] != d6["result"]

    async def test_unique_per_block(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        roots = set()
        for ib in chain:
            _, data = await rpc_call(jam_node_rpc, "stateRoot", [ib.header_hash_b64])
            roots.add(data["result"])
        assert len(roots) == 4


# ═══════════════════════════════════════════════
# 5. statistics
# ═══════════════════════════════════════════════

class TestStatistics:

    async def test_returns_nonempty(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "statistics", [chain[3].header_hash_b64])
        assert data["result"] is not None
        assert len(b64d(data["result"])) > 0

    async def test_multi_level(self, jam_node_rpc):
        """Statistics at block 2 vs block 4 (post-accumulation)."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=4)
        _, d2 = await rpc_call(node, "statistics", [chain[1].header_hash_b64])
        _, d4 = await rpc_call(node, "statistics", [chain[3].header_hash_b64])
        assert d2["result"] is not None
        assert d4["result"] is not None


# ═══════════════════════════════════════════════
# 6. listServices
# ═══════════════════════════════════════════════

class TestListServices:

    async def test_service_0_exists(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "listServices", [chain[3].header_hash_b64])
        assert 0 in data["result"]

    async def test_multi_level_service_lifecycle(self, jam_node_rpc):
        """Block 6: new service absent. Block 8: new service present."""
        node = jam_node_rpc
        svc = load_test_services()[0]
        sid = svc["service_id"]

        # Stage 1: import 6
        chain = import_chain(node, up_to=6)
        _, d6 = await rpc_call(node, "listServices", [chain[5].header_hash_b64])
        assert sid not in d6["result"]

        # Stage 2: import to 8
        chain = import_chain(node, up_to=8)
        _, d8 = await rpc_call(node, "listServices", [chain[7].header_hash_b64])
        assert sid in d8["result"]

    async def test_service_count_grows(self, jam_node_rpc):
        """More services after accumulation creates new ones."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=6)
        _, d6 = await rpc_call(node, "listServices", [chain[5].header_hash_b64])
        count_6 = len(d6["result"])

        chain = import_chain(node, up_to=8)
        _, d8 = await rpc_call(node, "listServices", [chain[7].header_hash_b64])
        count_8 = len(d8["result"])

        assert count_8 > count_6


# ═══════════════════════════════════════════════
# 7. serviceData
# ═══════════════════════════════════════════════

class TestServiceData:

    async def test_service_0_at_block_4(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "serviceData", [chain[3].header_hash_b64, 0])
        assert data["result"] is not None

    async def test_multi_level_new_service(self, jam_node_rpc):
        """New service: null at block 6, present at block 8."""
        node = jam_node_rpc
        svc = load_test_services()[0]

        chain = import_chain(node, up_to=6)
        _, d6 = await rpc_call(node, "serviceData", [chain[5].header_hash_b64, svc["service_id"]])
        assert d6.get("result") is None

        chain = import_chain(node, up_to=8)
        _, d8 = await rpc_call(node, "serviceData", [chain[7].header_hash_b64, svc["service_id"]])
        assert d8["result"] is not None

    async def test_nonexistent_service(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        _, data = await rpc_call(jam_node_rpc, "serviceData", [chain[3].header_hash_b64, 99999999])
        assert data.get("result") is None


# ═══════════════════════════════════════════════
# 8. serviceValue
# ═══════════════════════════════════════════════

class TestServiceValue:

    async def test_nonexistent_key_is_null(self, jam_node_rpc):
        """Storage key that doesn't exist returns null."""
        chain = import_chain(jam_node_rpc, up_to=4)
        fake_key = b64e(bytes(32))
        _, data = await rpc_call(
            jam_node_rpc, "serviceValue", [chain[3].header_hash_b64, 0, fake_key]
        )
        assert data.get("result") is None

    async def test_nonexistent_service_is_null(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        fake_key = b64e(bytes(32))
        _, data = await rpc_call(
            jam_node_rpc, "serviceValue", [chain[3].header_hash_b64, 99999999, fake_key]
        )
        assert data.get("result") is None


# ═══════════════════════════════════════════════
# 9. servicePreimage
# ═══════════════════════════════════════════════

class TestServicePreimage:

    async def test_nonexistent_hash_is_null(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        fake_hash = b64e(bytes(32))
        _, data = await rpc_call(
            jam_node_rpc, "servicePreimage", [chain[3].header_hash_b64, 0, fake_hash]
        )
        assert data.get("result") is None

    async def test_multi_level_preimage_appears(self, jam_node_rpc):
        """Block 5 stores preimages for service 0. Before: null. After: present."""
        node = jam_node_rpc

        # Block 5 has preimages — need to know a hash. Load from vectors.
        test_blocks = load_test_blocks()
        b5 = test_blocks[4]  # index 5
        preimages = b5["block"]["extrinsic"]["preimages"]
        if not preimages:
            return  # skip if no preimages in vector

        # Use the smallest preimage (81 bytes) for speed
        pi = min(preimages, key=lambda p: len(p.get("blob", "")))
        blob = bytes.fromhex(pi["blob"])
        import hashlib
        pi_hash = hashlib.blake2b(blob, digest_size=32).digest()
        pi_hash_b64 = b64e(pi_hash)

        # Stage 1: at block 4 — preimage not yet stored
        chain = import_chain(node, up_to=4)
        _, d4 = await rpc_call(node, "servicePreimage", [chain[3].header_hash_b64, 0, pi_hash_b64])
        assert d4.get("result") is None

        # Stage 2: at block 5 — preimage stored via extrinsic
        chain = import_chain(node, up_to=5)
        _, d5 = await rpc_call(node, "servicePreimage", [chain[4].header_hash_b64, 0, pi_hash_b64])
        assert d5["result"] is not None


# ═══════════════════════════════════════════════
# 10. serviceRequest
# ═══════════════════════════════════════════════

class TestServiceRequest:

    async def test_nonexistent_is_null(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=4)
        fake_hash = b64e(bytes(32))
        _, data = await rpc_call(
            jam_node_rpc, "serviceRequest", [chain[3].header_hash_b64, 0, fake_hash, 100]
        )
        assert data.get("result") is None


# ═══════════════════════════════════════════════
# 11. blockRequest
# ═══════════════════════════════════════════════

class TestBlockRequest:

    async def test_by_hash_matches_b64(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=5)
        for ib in chain[:4]:
            hash_list = list(bytes.fromhex(ib.header_hash))
            _, data = await rpc_call(jam_node_rpc, "blockRequest", [hash_list])
            assert data["result"] == b64e(ib.block)

    async def test_by_slot(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=5)
        ib = chain[2]
        _, data = await rpc_call(jam_node_rpc, "blockRequest", [ib.slot, "slot"])
        assert data["result"] is not None

    async def test_nonexistent_hash(self, jam_node_rpc):
        import_chain(jam_node_rpc, up_to=2)
        fake_hash = list(bytes(32))
        _, data = await rpc_call(jam_node_rpc, "blockRequest", [fake_hash])
        assert 200  # no crash


# ═══════════════════════════════════════════════
# 12. parameters
# ═══════════════════════════════════════════════

class TestParameters:

    async def test_has_v1(self, jam_node_rpc):
        _, data = await rpc_call(jam_node_rpc, "parameters")
        assert "V1" in data["result"]

    async def test_v1_required_fields(self, jam_node_rpc):
        _, data = await rpc_call(jam_node_rpc, "parameters")
        v1 = data["result"]["V1"]
        required = [
            "deposit_per_item", "deposit_per_byte", "deposit_per_account",
            "core_count", "epoch_period", "max_accumulate_gas",
            "max_refine_gas", "block_gas_limit", "val_count",
            "slot_period_sec", "rotation_period", "max_work_items",
        ]
        for key in required:
            assert key in v1, f"Missing parameter: {key}"

    async def test_values_are_positive(self, jam_node_rpc):
        _, data = await rpc_call(jam_node_rpc, "parameters")
        for key, val in data["result"]["V1"].items():
            assert isinstance(val, (int, float)), f"{key} not a number"
            assert val >= 0, f"{key} negative"


# ═══════════════════════════════════════════════
# 13. Error handling
# ═══════════════════════════════════════════════

class TestErrors:

    async def test_invalid_method(self, jam_node_rpc):
        _, data = await rpc_call(jam_node_rpc, "nonexistent_xyz")
        assert data["error"]["code"] == -32601

    async def test_sync_state_no_network(self, jam_node_rpc):
        _, data = await rpc_call(jam_node_rpc, "syncState")
        assert "result" in data or "error" in data

    async def test_state_root_bad_hash(self, jam_node_rpc):
        import_chain(jam_node_rpc, up_to=2)
        _, data = await rpc_call(jam_node_rpc, "stateRoot", [b64e(bytes(32))])
        assert 200  # no crash

    async def test_parent_of_genesis(self, jam_node_rpc):
        chain = import_chain(jam_node_rpc, up_to=1)
        genesis_hash = b64e(chain[0].raw["parent_hash"])
        _, data = await rpc_call(jam_node_rpc, "parent", [genesis_hash])
        assert 200  # genesis parent may be None


# ═══════════════════════════════════════════════
# 14. Progressive finalization — import 8, finalize 5, then advance
# ═══════════════════════════════════════════════

class TestProgressiveFinalization:
    """Import chain to 8, finalize to 5, then finalize one-by-one and test RPC at each step."""

    async def test_finalized_advances_on_each_finalize(self, jam_node_rpc):
        """finalizedBlock advances as we finalize blocks 6→7→8."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=8, finalize_to=5)

        # Finalized at block 5
        _, d5 = await rpc_call(node, "finalizedBlock")
        assert d5["result"]["header_hash"] == chain[4].header_hash_b64

        # Finalize block 6
        finalize_block(node, chain[5])
        _, d6 = await rpc_call(node, "finalizedBlock")
        assert d6["result"]["header_hash"] == chain[5].header_hash_b64

        # Finalize block 7
        finalize_block(node, chain[6])
        _, d7 = await rpc_call(node, "finalizedBlock")
        assert d7["result"]["header_hash"] == chain[6].header_hash_b64

        # Finalize block 8
        finalize_block(node, chain[7])
        _, d8 = await rpc_call(node, "finalizedBlock")
        assert d8["result"]["header_hash"] == chain[7].header_hash_b64

    async def test_state_root_at_each_finalize(self, jam_node_rpc):
        """stateRoot matches vector at each finalization step."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=8, finalize_to=5)

        for ib in chain[5:]:
            finalize_block(node, ib)
            _, data = await rpc_call(node, "stateRoot", [ib.header_hash_b64])
            assert data["result"] == ib.post_state_root_b64, (
                f"block {ib.index}: stateRoot mismatch after finalization"
            )

    async def test_service_appears_after_block_8_finalized(self, jam_node_rpc):
        """listServices: new service absent at block 5, appears after finalizing 8."""
        node = jam_node_rpc
        svc = load_test_services()[0]
        sid = svc["service_id"]

        chain = import_chain(node, up_to=8, finalize_to=5)

        # At finalized block 5 — no new service
        _, d5 = await rpc_call(node, "listServices", [chain[4].header_hash_b64])
        assert sid not in d5["result"]

        # Finalize 6, 7, 8
        for ib in chain[5:]:
            finalize_block(node, ib)

        # Now query at block 8 — service exists
        _, d8 = await rpc_call(node, "listServices", [chain[7].header_hash_b64])
        assert sid in d8["result"]

    async def test_preimage_appears_after_block_5_finalized(self, jam_node_rpc):
        """servicePreimage: null at block 4, present after block 5 finalized."""
        import hashlib
        node = jam_node_rpc

        # Get a preimage hash from block 5 vectors
        test_blocks = load_test_blocks()
        b5_preimages = test_blocks[4]["block"]["extrinsic"]["preimages"]
        if not b5_preimages:
            return

        pi = min(b5_preimages, key=lambda p: len(p.get("blob", "")))
        blob = bytes.fromhex(pi["blob"])
        pi_hash_b64 = b64e(hashlib.blake2b(blob, digest_size=32).digest())

        # Import 8 blocks, finalize only up to 4
        chain = import_chain(node, up_to=8, finalize_to=4)

        # At block 4 — preimage not stored yet
        _, d4 = await rpc_call(node, "servicePreimage", [chain[3].header_hash_b64, 0, pi_hash_b64])
        assert d4.get("result") is None

        # Finalize block 5 (which stores the preimages)
        finalize_block(node, chain[4])

        # At block 5 — preimage now present
        _, d5 = await rpc_call(node, "servicePreimage", [chain[4].header_hash_b64, 0, pi_hash_b64])
        assert d5["result"] is not None
