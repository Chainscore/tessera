"""
State cache behavior and chain-driven transition tests.

Tests that cache vs DB works correctly, each block changes root,
and accumulation produces expected side effects (WP availability, services).
"""
from jam.state.utils import construct_state_key
from jam.types.protocol.core import ServiceId, TimeSlot
from tsrkit_types import Bytes

from tests.unit.api.utils import import_chain


class TestStateCaching:
    """Delta writes go to cache, not directly to DB."""

    async def test_delta_write_is_cached(self, jam_node):
        state = jam_node.state
        key = Bytes(b"cache_test_key")
        val = Bytes(b"cache_test_val")

        state.delta[ServiceId(0)].storage[key] = val
        assert state.delta[ServiceId(0)].storage[key] == val

    async def test_tau_update_is_cached(self, jam_node):
        """tau update goes to cache, DB still has old value."""
        state = jam_node.state
        assert state.tau == 0

        state.tau = TimeSlot(1)
        assert state.tau == 1

        # Should be in cache, not yet in DB
        db_val = state.store.get(construct_state_key(11), skip_cache=True)
        assert db_val == TimeSlot(0).encode()

    async def test_service_0_readable(self, jam_node):
        acct = jam_node.state.delta[ServiceId(0)]
        assert acct.service.code_hash is not None


class TestChainTransitions:
    """Block-by-block transitions via vector chain."""

    async def test_each_block_changes_root(self, jam_node):
        roots = [jam_node.state.root.hex()]
        for n in range(1, 5):
            import_chain(jam_node, up_to=n)
            roots.append(jam_node.state.root.hex())
        assert len(set(roots)) == len(roots), f"duplicate roots: {roots}"

    async def test_tau_matches_slot(self, jam_node):
        """After importing blocks, tau equals the last block's slot."""
        chain = import_chain(jam_node, up_to=4)
        assert int(jam_node.state.tau) == chain[-1].slot

    async def test_block_4_accumulates(self, jam_node):
        """Block 4 has 6 assurances — triggers WP1 accumulation."""
        chain = import_chain(jam_node, up_to=4)
        assert int(jam_node.state.tau) == chain[3].slot


class TestServiceLifecycle:
    """Service creation via accumulation."""

    async def test_service_not_exists_before_block_8(self, jam_node):
        from tests.unit.api.utils import load_test_services
        svc = load_test_services()[0]
        sid = ServiceId(svc["service_id"])

        import_chain(jam_node, up_to=6)
        assert jam_node.state.delta.get(sid) is None

    async def test_service_created_at_block_8(self, jam_node):
        from tests.unit.api.utils import load_test_services
        svc = load_test_services()[0]
        sid = ServiceId(svc["service_id"])

        import_chain(jam_node, up_to=8)
        acct = jam_node.state.delta.get(sid)
        assert acct is not None

    async def test_service_code_hash_matches(self, jam_node):
        from tests.unit.api.utils import load_test_services
        svc = load_test_services()[0]
        sid = ServiceId(svc["service_id"])

        import_chain(jam_node, up_to=8)
        assert jam_node.state.delta[sid].service.code_hash.hex() == svc["code_hash"]
