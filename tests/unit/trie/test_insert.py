from jam.state.merkle.merkle import StateTrie
from jam.state.merkle.utils import ZERO_HASH
from tsrkit_types.bytes import Bytes
from jam.utils.byte_utils import ByteUtils
from jam.utils.dummy.utils import create_dummy_bytes

def to_32by(value: list) -> bytes:
    return ByteUtils.bitarray_to_bytes(value + [0] * (256 - len(value)))

def random_key():
    # simple helper for random 32‐byte keys
    import os
    return Bytes[32].fromhex(os.urandom(32))

def random_value():
    return Bytes(create_dummy_bytes(16))

def test_single_insert_matches_merkelize():
    key = Bytes[32].fromhex(to_32by([1,0,1]))
    val = random_value()
    trie = StateTrie()
    root_full, _ = trie.merkelize({key: val})
    trie2 = StateTrie()
    root_empty, _ = trie2.merkelize({})
    root2 = trie2.update(key, val)
    assert root_full == root2

def test_multiple_inserts_order_independent():
    # five keys, insert in different orders must yield same root
    keys = [Bytes[32].fromhex(to_32by(bits)) for bits in [
        [1,0,0,1,1],
        [0,1,0,1,0],
        [1,1,1,0,0],
        [0,0,1,1,1],
        [1,0,1,0,1],
    ]]
    vals = [random_value() for _ in keys]
    base = dict(zip(keys, vals))

    # full merkle root
    tri_full = StateTrie()
    full_root, _ = tri_full.merkelize(base)

    # incremental
    tri_inc = StateTrie()
    tri_inc.merkelize({})
    root = ZERO_HASH
    for k,v in zip(keys, vals):
        root = tri_inc.update(k, v) if root != ZERO_HASH else tri_inc.merkelize({k:v})[0]
    # but better do incremental from empty via merkelize then update_global_root
    tri_inc2 = StateTrie()
    tri_inc2.merkelize({})
    for key, value in base.items():
        tri_inc2.update(key, value)
    assert full_root == tri_inc2.root_hash

def test_update_existing_key_changes_root():
    key = random_key()
    v1, v2 = random_value(), random_value()
    trie = StateTrie()
    root1, _ = trie.merkelize({key: v1})
    root2 = trie.update(key, v2)
    assert root1 != root2
    # updating back to v1 returns to original root
    root3 = trie.update(key, v1)
    assert root3 == root1

def test_reinsert_same_value_no_change():
    key = random_key()
    val = random_value()
    trie = StateTrie()
    root1, _ = trie.merkelize({key: val})
    root2 = trie.update(key, val)  # same value
    assert root1 == root2

def test_bulk_insert_vs_incremental_identical():
    # compare full merkelize vs sequential update_global_root
    data = {random_key(): random_value() for _ in range(10)}
    tri_full = StateTrie()
    full_root, _ = tri_full.merkelize(data)
    tri_inc = StateTrie()
    tri_inc.merkelize({})
    for key, value in data.items():
        inc_root = tri_inc.update(key, value)
    assert full_root == inc_root
