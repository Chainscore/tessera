"""
State load + persistence tests with finalized vs non-finalized blocks.

Core pattern: import chain up to 8, finalize only up to 5.
Then finalize blocks 6, 7, 8 one-by-one and verify at each step.

Tests:
- Load finalized (settled) state
- Load pre-final (earlier settled) state
- Load post-final (stashed-only) state
- Progressive finalization — finalize one block at a time and verify
- Finality head correctness
- Block persistence and parent chain
"""
from jam.state.state import State
from jam.block.block import Block
from jam.types import HeaderHash

from tests.unit.api.utils import import_chain, finalize_block


FINALIZED_BLOCK = 5


class TestLoadFinal:
    """Finalized block state loading — settled into DB."""

    async def test_finalized_head(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        fb = jam_node.grandpa.load_final()
        assert fb.header.hash().hex() == chain[FINALIZED_BLOCK - 1].header_hash

    async def test_finalized_state_root(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        fb = jam_node.grandpa.load_final()
        state = State.load(jam_node, fb.header.hash())
        assert state.root.hex() == chain[FINALIZED_BLOCK - 1].post_state_root


class TestLoadPreFinal:
    """Load state from blocks before the finalized tip — also settled."""

    async def test_each_pre_final(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        for ib in chain[:FINALIZED_BLOCK]:
            loaded = State.load(jam_node, HeaderHash.fromhex(ib.header_hash))
            assert loaded.root.hex() == ib.post_state_root, (
                f"block {ib.index}: pre-final root mismatch"
            )


class TestLoadPostFinal:
    """Load state from blocks after the finalized tip — stashed only."""

    async def test_each_post_final(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        for ib in chain[FINALIZED_BLOCK:]:
            loaded = State.load(jam_node, HeaderHash.fromhex(ib.header_hash))
            assert loaded.root.hex() == ib.post_state_root, (
                f"block {ib.index}: post-final root mismatch"
            )


class TestProgressiveFinalization:
    """Import chain to 8 with finalize_to=5, then finalize 6→7→8 one by one."""

    async def test_finalize_block_6(self, jam_node):
        """Finalize block 6, verify finalized head advances."""
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)

        # Before: finalized at block 5
        fb = jam_node.grandpa.load_final()
        assert fb.header.hash().hex() == chain[FINALIZED_BLOCK - 1].header_hash

        # Finalize block 6
        finalize_block(jam_node, chain[5])

        # After: finalized at block 6
        fb = jam_node.grandpa.load_final()
        assert fb.header.hash().hex() == chain[5].header_hash

    async def test_finalize_6_then_7(self, jam_node):
        """Finalize blocks 6 and 7, state root matches at each step."""
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)

        finalize_block(jam_node, chain[5])
        s6 = State.load(jam_node, HeaderHash.fromhex(chain[5].header_hash))
        assert s6.root.hex() == chain[5].post_state_root

        finalize_block(jam_node, chain[6])
        fb = jam_node.grandpa.load_final()
        assert fb.header.hash().hex() == chain[6].header_hash

        s7 = State.load(jam_node, HeaderHash.fromhex(chain[6].header_hash))
        assert s7.root.hex() == chain[6].post_state_root

    async def test_finalize_all_remaining(self, jam_node):
        """Finalize 6→7→8, verify finalized head is block 8."""
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)

        for ib in chain[FINALIZED_BLOCK:]:
            finalize_block(jam_node, ib)

            fb = jam_node.grandpa.load_final()
            assert fb.header.hash().hex() == ib.header_hash

            loaded = State.load(jam_node, HeaderHash.fromhex(ib.header_hash))
            assert loaded.root.hex() == ib.post_state_root

    async def test_service_appears_after_finalize_8(self, jam_node):
        """Service 1287605561 appears only after block 8 is finalized."""
        from jam.types.protocol.core import ServiceId
        from tests.unit.api.utils import load_test_services
        svc = load_test_services()[0]
        sid = ServiceId(svc["service_id"])

        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)

        # Finalized state (block 5) — no new service
        assert jam_node.state.delta.get(sid) is None

        # Finalize 6, 7, 8 one by one
        for ib in chain[FINALIZED_BLOCK:]:
            finalize_block(jam_node, ib)

        # Now finalized state includes block 8 accumulation
        acct = jam_node.state.delta.get(sid)
        assert acct is not None
        assert acct.service.code_hash.hex() == svc["code_hash"]


class TestUniqueRoots:

    async def test_each_block_has_unique_root(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        roots = set()
        for ib in chain:
            loaded = State.load(jam_node, HeaderHash.fromhex(ib.header_hash))
            roots.add(loaded.root.hex())
        assert len(roots) == len(chain)


class TestBlockPersistence:
    """All imported blocks are saved in DB regardless of finality."""

    async def test_all_blocks_saved(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        db = jam_node.settings.main_db
        for ib in chain:
            loaded = Block.load(bytes.fromhex(ib.header_hash), db)
            assert loaded is not None, f"block {ib.index} not in DB"
            assert loaded.header.hash().hex() == ib.header_hash

    async def test_parent_chain(self, jam_node):
        chain = import_chain(jam_node, up_to=8, finalize_to=FINALIZED_BLOCK)
        db = jam_node.settings.main_db
        for i in range(1, len(chain)):
            block = Block.load(bytes.fromhex(chain[i].header_hash), db)
            parent = block.load_parent(db)
            assert parent is not None
            assert parent.header.hash().hex() == chain[i - 1].header_hash
