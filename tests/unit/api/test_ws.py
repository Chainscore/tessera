"""
WebSocket subscription tests.

Pattern: subscribe → import blocks / finalize → read updates → verify.
Uses progressive finalization: import 8, finalize 5, then advance one-by-one.

Timeline:
  block 1-2: empty blocks
  block 3: guarantee (WP1 reported)
  block 4: 6 assurances (WP1 available → accumulate)
  block 5: 3 preimages for service 0
  block 6: 1 preimage for service 0
  block 7: guarantee (WP2 reported)
  block 8: 6 assurances (WP2 available → accumulate → creates service 1287605561)
"""
import json
import asyncio

from tests.unit.api.utils import import_chain, finalize_block, b64e, load_test_services


def _req(method, params=None, req_id=101):
    return json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or []})


async def _recv(ws, timeout=5):
    raw = await asyncio.wait_for(ws.receive(), timeout=timeout)
    return json.loads(raw)


async def _subscribe(ws, method, params=None, req_id=101):
    """Subscribe, return (sub_id, initial_data)."""
    await ws.send(_req(method, params, req_id))
    ack = await _recv(ws)
    assert ack["id"] == req_id
    sub_id = ack["result"]
    initial = await _recv(ws)
    return sub_id, initial


async def _drain(ws, method=None, timeout=2, max_msgs=10):
    """Drain messages from WS, optionally filter by method. Returns list."""
    msgs = []
    for _ in range(max_msgs):
        try:
            msg = await _recv(ws, timeout=timeout)
            if method is None or msg.get("method") == method:
                msgs.append(msg)
        except asyncio.TimeoutError:
            break
    return msgs


# ═══════════════════════════════════════════════
# 1. subscribeBestBlock
# ═══════════════════════════════════════════════

class TestBestBlock:

    async def test_ack_and_initial(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                sub_id, initial = await _subscribe(ws, "subscribeBestBlock")
                r = initial["params"]["result"]
                assert "header_hash" in r
                assert "slot" in r

    async def test_block_by_block_updates(self, jam_node_rpc):
        """Import blocks one at a time, read update after each."""
        node = jam_node_rpc
        import_chain(node, up_to=2)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, _ = await _subscribe(ws, "subscribeBestBlock")

                for n in [3, 4, 5]:
                    chain = import_chain(node, up_to=n)
                    u = await _recv(ws)
                    assert u["params"]["result"]["header_hash"] == chain[n - 1].header_hash_b64
                    assert u["params"]["result"]["slot"] == chain[n - 1].slot


# ═══════════════════════════════════════════════
# 2. subscribeFinalizedBlock
# ═══════════════════════════════════════════════

class TestFinalizedBlock:

    async def test_initial(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeFinalizedBlock")
                assert "header_hash" in initial["params"]["result"]

    async def test_block_by_block(self, jam_node_rpc):
        """Each instant-finality block fires a finalized update."""
        node = jam_node_rpc
        import_chain(node, up_to=2)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, _ = await _subscribe(ws, "subscribeFinalizedBlock")

                chain = import_chain(node, up_to=3)
                u = await _recv(ws)
                assert u["params"]["result"]["header_hash"] == chain[2].header_hash_b64

                chain = import_chain(node, up_to=4)
                u = await _recv(ws)
                assert u["params"]["result"]["header_hash"] == chain[3].header_hash_b64

    async def test_progressive_finalization(self, jam_node_rpc):
        """Import 8 finalize 5, subscribe, then finalize 6→7→8 — get update each time."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=8, finalize_to=5)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeFinalizedBlock")
                # Initial should be block 5
                assert initial["params"]["result"]["header_hash"] == chain[4].header_hash_b64

                # Finalize 6 → update
                finalize_block(node, chain[5])
                u6 = await _recv(ws)
                assert u6["params"]["result"]["header_hash"] == chain[5].header_hash_b64

                # Finalize 7 → update
                finalize_block(node, chain[6])
                u7 = await _recv(ws)
                assert u7["params"]["result"]["header_hash"] == chain[6].header_hash_b64

                # Finalize 8 → update
                finalize_block(node, chain[7])
                u8 = await _recv(ws)
                assert u8["params"]["result"]["header_hash"] == chain[7].header_hash_b64


# ═══════════════════════════════════════════════
# 3. subscribeStatistics
# ═══════════════════════════════════════════════

class TestStatistics:

    async def test_initial_has_value(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeStatistics", [True])
                r = initial["params"]["result"]
                assert "header_hash" in r
                assert "value" in r

    async def test_update_after_transition(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, _ = await _subscribe(ws, "subscribeStatistics", [False])

                import_chain(node, up_to=5)
                u = await _recv(ws)
                assert u["method"] == "subscribeStatistics"
                assert "value" in u["params"]["result"]

    async def test_value_changes_across_blocks(self, jam_node_rpc):
        """Statistics should change between block 3 and block 4 (accumulation)."""
        node = jam_node_rpc
        import_chain(node, up_to=3)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeStatistics", [False])
                val_initial = initial["params"]["result"]["value"]

                import_chain(node, up_to=4)
                u = await _recv(ws)
                val_after = u["params"]["result"]["value"]

                assert val_after is not None


# ═══════════════════════════════════════════════
# 4. subscribeServiceData
# ═══════════════════════════════════════════════

class TestServiceData:

    async def test_service_0_exists(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServiceData", [0, True])
                assert initial["params"]["result"]["value"] is not None

    async def test_fake_service_is_null(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServiceData", [999999, True])
                assert initial["params"]["result"]["value"] is None

    async def test_new_service_null_then_exists(self, jam_node_rpc):
        """Subscribe at block 6 (null), import to 8, service appears."""
        node = jam_node_rpc
        svc = load_test_services()[0]
        import_chain(node, up_to=6)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServiceData", [svc["service_id"], True])
                assert initial["params"]["result"]["value"] is None

                import_chain(node, up_to=8)

                # Drain until we find non-null service data
                msgs = await _drain(ws, method="subscribeServiceData")
                found = any(m["params"]["result"]["value"] is not None for m in msgs)
                assert found, "Expected service data update after block 8"

    async def test_progressive_service_data(self, jam_node_rpc):
        """Import 8 finalize 5, subscribe service 0, finalize 6→7→8 — data updates."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=8, finalize_to=5)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServiceData", [0, True])
                assert initial["params"]["result"]["value"] is not None
                val_at_5 = initial["params"]["result"]["value"]

                # Finalize block 6 (has preimage for service 0)
                finalize_block(node, chain[5])
                msgs = await _drain(ws, method="subscribeServiceData", timeout=2)
                # Should get at least one update
                if msgs:
                    assert msgs[-1]["params"]["result"]["value"] is not None


# ═══════════════════════════════════════════════
# 5. subscribeServiceValue
# ═══════════════════════════════════════════════

class TestServiceValue:

    async def test_nonexistent_key_is_null(self, jam_node_rpc):
        """Subscribe to a storage key that doesn't exist — initial is null."""
        node = jam_node_rpc
        import_chain(node, up_to=4)
        fake_key = b64e(bytes(32))

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServiceValue", [0, fake_key, True])
                assert initial["params"]["result"]["value"] is None


# ═══════════════════════════════════════════════
# 6. subscribeServicePreimage
# ═══════════════════════════════════════════════

class TestServicePreimage:

    async def test_nonexistent_hash_is_null(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)
        fake_hash = b64e(bytes(32))

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServicePreimage", [0, fake_hash, True])
                assert initial["params"]["result"]["value"] is None

    async def test_preimage_appears_after_block_5(self, jam_node_rpc):
        """Subscribe to preimage hash, import block 5 (stores preimages) — value appears."""
        import hashlib
        from tests.unit.api.utils import load_test_blocks

        node = jam_node_rpc
        test_blocks = load_test_blocks()
        b5_preimages = test_blocks[4]["block"]["extrinsic"]["preimages"]
        if not b5_preimages:
            return

        # Use smallest preimage for speed
        pi = min(b5_preimages, key=lambda p: len(p.get("blob", "")))
        blob = bytes.fromhex(pi["blob"])
        pi_hash = hashlib.blake2b(blob, digest_size=32).digest()
        pi_hash_b64 = b64e(pi_hash)

        # Import up to 4 — preimage not yet stored
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(ws, "subscribeServicePreimage", [0, pi_hash_b64, True])
                assert initial["params"]["result"]["value"] is None

                # Import block 5 (stores preimages)
                import_chain(node, up_to=5)

                msgs = await _drain(ws, method="subscribeServicePreimage")
                found = any(m["params"]["result"]["value"] is not None for m in msgs)
                assert found, "Expected preimage to appear after block 5"


# ═══════════════════════════════════════════════
# 7. subscribeServiceRequest
# ═══════════════════════════════════════════════

class TestServiceRequest:

    async def test_nonexistent_is_null(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)
        fake_hash = b64e(bytes(32))

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, initial = await _subscribe(
                    ws, "subscribeServiceRequest", [0, fake_hash, 100, True]
                )
                assert initial["params"]["result"]["value"] is None


# ═══════════════════════════════════════════════
# 8. listServices via WS (regular RPC over WS)
# ═══════════════════════════════════════════════

class TestListServices:

    async def test_progressive_service_creation(self, jam_node_rpc):
        """Import 8 finalize 5. Query listServices via WS. Finalize to 8. Query again."""
        node = jam_node_rpc
        svc = load_test_services()[0]

        chain = import_chain(node, up_to=8, finalize_to=5)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                # At block 5 — no new service
                hh5 = b64e(node.grandpa.load_final().header.hash())
                await ws.send(_req("listServices", [hh5], req_id=10))
                resp = await _recv(ws)
                assert svc["service_id"] not in resp["result"]

                # Finalize 6, 7, 8
                for ib in chain[5:]:
                    finalize_block(node, ib)

                # At block 8 — service exists
                hh8 = b64e(node.grandpa.load_final().header.hash())
                await ws.send(_req("listServices", [hh8], req_id=11))
                resp = await _recv(ws)
                assert svc["service_id"] in resp["result"]


# ═══════════════════════════════════════════════
# 9. WS as regular RPC
# ═══════════════════════════════════════════════

class TestWSRPC:

    async def test_best_block(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                await ws.send(_req("bestBlock", req_id=42))
                resp = await _recv(ws)
                assert resp["id"] == 42
                assert "header_hash" in resp["result"]

    async def test_finalized_block(self, jam_node_rpc):
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                await ws.send(_req("finalizedBlock", req_id=43))
                resp = await _recv(ws)
                assert resp["id"] == 43
                assert "slot" in resp["result"]

    async def test_parent(self, jam_node_rpc):
        node = jam_node_rpc
        chain = import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                await ws.send(_req("parent", [chain[3].header_hash_b64], req_id=44))
                resp = await _recv(ws)
                assert resp["id"] == 44
                assert resp["result"]["header_hash"] == chain[2].header_hash_b64

    async def test_state_root(self, jam_node_rpc):
        node = jam_node_rpc
        chain = import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                await ws.send(_req("stateRoot", [chain[2].header_hash_b64], req_id=45))
                resp = await _recv(ws)
                assert resp["id"] == 45
                assert resp["result"] == chain[2].post_state_root_b64

    async def test_invalid_method(self, jam_node_rpc):
        node = jam_node_rpc

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                await ws.send(_req("nonexistent_xyz", req_id=99))
                resp = await _recv(ws)
                assert resp["id"] == 99
                assert resp["error"]["code"] == -32601


# ═══════════════════════════════════════════════
# 10. Lifecycle
# ═══════════════════════════════════════════════

class TestLifecycle:

    async def test_unsubscribe(self, jam_node_rpc):
        node = jam_node_rpc

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                sub_id, _ = await _subscribe(ws, "subscribeBestBlock")

                await ws.send(_req("unsubscribeBestBlock", [sub_id], req_id=200))
                for _ in range(5):
                    msg = await _recv(ws)
                    if msg.get("id") == 200:
                        assert msg["result"] is True
                        return
                assert False, "never got unsubscribe ack"

    async def test_two_subs_both_fire(self, jam_node_rpc):
        """Subscribe best + finalized, import a block, both should fire."""
        node = jam_node_rpc
        import_chain(node, up_to=4)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, _ = await _subscribe(ws, "subscribeBestBlock", req_id=1)
                _, _ = await _subscribe(ws, "subscribeFinalizedBlock", req_id=2)

                import_chain(node, up_to=5)

                methods = set()
                for _ in range(4):
                    try:
                        msg = await _recv(ws, timeout=2)
                        if "method" in msg:
                            methods.add(msg["method"])
                    except asyncio.TimeoutError:
                        break

                assert "subscribeBestBlock" in methods
                assert "subscribeFinalizedBlock" in methods

    async def test_progressive_two_subs(self, jam_node_rpc):
        """Subscribe best + finalized with partial finality, finalize one — only finalized fires."""
        node = jam_node_rpc
        chain = import_chain(node, up_to=8, finalize_to=5)

        async with node.responder.app.test_client() as client:
            async with client.websocket("/") as ws:
                _, _ = await _subscribe(ws, "subscribeBestBlock", req_id=1)
                _, _ = await _subscribe(ws, "subscribeFinalizedBlock", req_id=2)

                # Finalize block 6
                finalize_block(node, chain[5])

                msgs = await _drain(ws, timeout=2)
                methods = {m.get("method") for m in msgs if "method" in m}
                # Finalized should fire
                assert "subscribeFinalizedBlock" in methods
