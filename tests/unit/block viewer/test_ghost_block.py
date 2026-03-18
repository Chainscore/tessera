"""BlockView (ghost block tree) unit tests.

Tests the ghost tree: record, finalize, best_block, mark_as_audited,
load_ghost, load_block_w_ts.

Key behavior: finalization evicts the previous final from _index_map,
so only the current final + unfinalized descendants remain in the tree.
"""
import pytest

pytestmark = pytest.mark.unit

from jam.block.block_view import BlockStatus
from jam.types.protocol.crypto import HeaderHash
from tests.unit.api.utils import import_chain, finalize_block


class TestGhostBlockTree:

    async def test_genesis_is_final(self, jam_node):
        assert jam_node.ledger.final is not None
        assert jam_node.ledger.final.status == BlockStatus.final

    async def test_unfinalized_blocks_in_index(self, jam_node):
        chain = import_chain(jam_node, up_to=4, finalize_to=1)
        ledger = jam_node.ledger
        # Blocks 2-4 are stashed (not finalized) — should be in index
        for ib in chain[1:]:
            ghost = ledger.load_ghost(HeaderHash.fromhex(ib.header_hash))
            assert ghost is not None, f"block {ib.index} should be in ghost tree"

    async def test_finalized_blocks_evicted(self, jam_node):
        chain = import_chain(jam_node, up_to=4)
        ledger = jam_node.ledger
        # All finalized — only the last (block 4) remains as current final
        ghost_1 = ledger.load_ghost(HeaderHash.fromhex(chain[0].header_hash))
        assert ghost_1 is None, "block 1 should be evicted after later blocks finalized"

        ghost_4 = ledger.load_ghost(HeaderHash.fromhex(chain[3].header_hash))
        assert ghost_4 is not None, "current final block should be in index"

    async def test_current_final_always_in_index(self, jam_node):
        chain = import_chain(jam_node, up_to=6)
        hh = HeaderHash.fromhex(chain[5].header_hash)
        assert jam_node.ledger.load_ghost(hh) is not None


class TestFinalization:

    async def test_finalize_advances_final(self, jam_node):
        chain = import_chain(jam_node, up_to=4, finalize_to=2)
        ledger = jam_node.ledger
        assert ledger.final.header == HeaderHash.fromhex(chain[1].header_hash)

        finalize_block(jam_node, chain[2])
        assert ledger.final.header == HeaderHash.fromhex(chain[2].header_hash)

    async def test_finalize_all_remaining(self, jam_node):
        chain = import_chain(jam_node, up_to=6, finalize_to=3)
        for ib in chain[3:]:
            finalize_block(jam_node, ib)
        assert jam_node.ledger.final.header == HeaderHash.fromhex(chain[5].header_hash)

    async def test_final_status(self, jam_node):
        chain = import_chain(jam_node, up_to=3)
        assert jam_node.ledger.final.status == BlockStatus.final


class TestBestBlock:

    async def test_best_at_genesis(self, jam_node):
        best = jam_node.ledger.best_block()
        assert best is not None
        assert best.status == BlockStatus.final

    async def test_best_follows_audited_chain(self, jam_node):
        chain = import_chain(jam_node, up_to=4)
        best = jam_node.ledger.best_block()
        assert best.slot >= jam_node.ledger.final.slot


class TestLoadByTimeslot:

    async def test_load_block_by_slot(self, jam_node):
        chain = import_chain(jam_node, up_to=4, finalize_to=1)
        # Block 3 is not finalized — still in index
        slot = chain[2].slot
        blocks = jam_node.ledger.load_block_w_ts(slot)
        assert len(blocks) >= 1
        assert any(b.header.slot == slot for b in blocks)

    async def test_nonexistent_slot(self, jam_node):
        import_chain(jam_node, up_to=2)
        assert len(jam_node.ledger.load_block_w_ts(999999)) == 0
