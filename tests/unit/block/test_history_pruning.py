from rockstore import RockStore

from jam.block import Block
from jam.block.block_view import BlockView, GhostBlock
from jam.models.protocol.core import TimeSlot
from jam.models.protocol.crypto import Hash, HeaderHash
from jam.state.storage import StateStorage
from jam.utils.constants import STATE_HISTORY_RETENTION


def _hh(slot: int) -> bytes:
    return bytes(Hash.blake2b(f"block-{slot}".encode()))


def _block_keys(hh: bytes):
    return (
        Block.get_storage_key_block(hh),
        Block.get_storage_key_meta(hh),
        StateStorage.get_storage_key(hh),
    )


def test_prune_history_drops_aged_blocks_and_keeps_window(db_path):
    kv = RockStore(db_path + "/main")
    head_slot = STATE_HISTORY_RETENTION + 50

    hashes = {}
    for slot in range(1, head_slot + 1):
        hh = _hh(slot)
        hashes[slot] = hh
        kv.put(Block.get_storage_key_slot(TimeSlot(slot)), hh)
        for key in _block_keys(hh):
            kv.put(key, b"x")

    view = BlockView()
    final = GhostBlock()
    final.slot = TimeSlot(head_slot)
    view.final = final

    view.prune_history(kv)

    threshold = head_slot - STATE_HISTORY_RETENTION
    assert view._pruned_upto_slot == threshold

    # Aged-out slots (<= threshold) are fully deleted.
    for slot in range(1, threshold + 1):
        assert kv.get(Block.get_storage_key_slot(TimeSlot(slot))) is None
        for key in _block_keys(hashes[slot]):
            assert kv.get(key) is None

    # Everything inside the retention window is untouched.
    for slot in range(threshold + 1, head_slot + 1):
        assert kv.get(Block.get_storage_key_slot(TimeSlot(slot))) == hashes[slot]
        for key in _block_keys(hashes[slot]):
            assert kv.get(key) == b"x"


def test_prune_history_is_incremental_and_idempotent(db_path):
    kv = RockStore(db_path + "/main")

    view = BlockView()
    view.final = GhostBlock()

    # Below the retention window: nothing to prune yet.
    view.final.slot = TimeSlot(STATE_HISTORY_RETENTION)
    view.prune_history(kv)
    assert view._pruned_upto_slot == 0

    # Advance the head; only the newly aged-out tail should be pruned.
    view.final.slot = TimeSlot(STATE_HISTORY_RETENTION + 10)
    view.prune_history(kv)
    assert view._pruned_upto_slot == 10

    # Re-running at the same finalized slot is a no-op.
    view.prune_history(kv)
    assert view._pruned_upto_slot == 10
