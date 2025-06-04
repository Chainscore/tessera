from copy import deepcopy

from jam.state.merkle.merkle import StateTrie
from tsrkit_types.bytes import Bytes

from tests.unit.trie.visualise import visualize_trie


def test_trie_update():
    """Test that updating a key in the trie produces the correct new root hash."""
    # Initial vector of key->value hex strings
    vector = {
        Bytes[32].fromhex("d7f99b746f23411983df92806725af8e5cb66eba9f200737accae4a1ab7f47b9"): Bytes.fromhex("24232437f5b3f2380ba9089bdbc45efaffbe386602cb1ecc2c17f1d0"),
        Bytes[32].fromhex("59ee947b94bcc05634d95efb474742f6cd6531766e44670ec987270a6b5a4211"): Bytes.fromhex("72fdb0c99cf47feb85b2dad01ee163139ee6d34a8d893029a200aff76f4be5930b9000a1bbb2dc2b6c79f8f3c19906c94a3472349817af21181c3eef6b"),
        Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2"):   Bytes.fromhex("8a0dafa9d6ae6177"),
        Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex("157b6c821169dacabcf26690df"),
        Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"): Bytes.fromhex("6a208734106f38b73880684b"),
    }
    # Create a modified vector where one key's value changes
    updated_vector = deepcopy(vector)
    key_to_update = Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19")
    new_value = Bytes.fromhex("8a0dafa9d6ae6177")
    updated_vector[key_to_update] = new_value

    # Build original trie and get its root
    trie = StateTrie()
    original_root, _ = trie.merkelize(vector)
    print("Initial trie", visualize_trie(trie))
    # Build updated trie and get expected root
    updated_trie = StateTrie()
    expected_root, _ = updated_trie.merkelize(updated_vector)

    # Perform in-place update on the original trie
    new_root = trie.update(key_to_update, new_value)

    print("Expected", visualize_trie(updated_trie))
    print("Actual", visualize_trie(trie))
    # The new root must equal the expected root
    assert new_root == expected_root
    assert trie.root_hash == expected_root


# def test_reinsert_same_value_no_change():
#     """Re-inserting the same value should not change the root."""
#     key = Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2")
#     val = Bytes.fromhex("8a0dafa9d6ae6177")
#     trie = StateTrie()
#     root1, _ = trie.merkelize({key: val})
#     root2 = trie.update(key, val)
#     assert root1 == root2
#
#
# def test_sequential_updates_multiple_keys():
#     """Sequentially updating multiple keys yields same as full merkelize on combined changes."""
#     # base vector
#     vector = {
#         Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex("157b6c821169dacabcf26690df"),
#         Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"): Bytes.fromhex("6a208734106f38b73880684b"),
#     }
#     # updates to apply
#     updates = {
#         Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex("abcdef"),
#         Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"): Bytes.fromhex("123456"),
#     }
#     # expected root via full merkelize
#     merged = {**vector, **updates}
#     trie_full = StateTrie()
#     expected_root, _ = trie_full.merkelize(merged)
#
#     # apply updates sequentially
#     trie = StateTrie()
#     trie.merkelize(vector)
#     root = None
#     for k, v in updates.items():
#         root = trie.update(k, v)
#
#     assert root == expected_root
#     assert trie.root_hash == expected_root
#
#
# def test_update_global_root_multiple():
#     """Test update of multiple keys at once via update_global_root."""
#     vector = {
#         Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2"): Bytes.fromhex("8a0dafa9d6ae6177"),
#         Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex("157b6c821169dacabcf26690df"),
#     }
#     updates = {
#         Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2"): Bytes.fromhex("ffffffff"),
#         Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex("000000"),
#     }
#     # expected root via full merkelize
#     merged = {**vector, **updates}
#     trie_full = StateTrie()
#     expected_root, _ = trie_full.merkelize(merged)
#
#     # update_global_root
#     trie = StateTrie()
#     trie.merkelize(vector)
#     for key, value in updates.items():
#         new_root = trie.update(key, value)
#
#     assert new_root == expected_root
#     assert trie.root_hash == expected_root
