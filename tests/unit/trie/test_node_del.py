from copy import deepcopy

from jam.utils.trie.merkle import StateTrie
from tsrkit_types.bytes import Bytes


def test_node_del():
    """Test that deleting a key in the trie produces the correct new root hash."""
    # Initial vector of key->value hex strings
    vector = {
        Bytes[32].fromhex(
            "d7f99b746f23411983df92806725af8e5cb66eba9f200737accae4a1ab7f47b9"
        ): Bytes.fromhex("24232437f5b3f2380ba9089bdbc45efaffbe386602cb1ecc2c17f1d0"),
        Bytes[32].fromhex(
            "59ee947b94bcc05634d95efb474742f6cd6531766e44670ec987270a6b5a4211"
        ): Bytes.fromhex(
            "72fdb0c99cf47feb85b2dad01ee163139ee6d34a8d893029a200aff76f4be5930b9000a1bbb2dc2b6c79f8f3c19906c94a3472349817af21181c3eef6b"
        ),
        Bytes[32].fromhex(
            "a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2"
        ): Bytes.fromhex("8a0dafa9d6ae6177"),
        Bytes[32].fromhex(
            "15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"
        ): Bytes.fromhex("157b6c821169dacabcf26690df"),
        Bytes[32].fromhex(
            "b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"
        ): Bytes.fromhex("6a208734106f38b73880684b"),
    }
    # Create a modified vector where one key's value changes
    updated_vector = deepcopy(vector)
    keyval_to_delete = (
        Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"),
        Bytes.fromhex("6a208734106f38b73880684b"),
    )
    del updated_vector[keyval_to_delete[0]]

    # Build original trie and get its root
    trie = StateTrie()
    original_root, _ = trie.merkelize(vector)
    # print("\noriginal root", original_root)

    # Build updated trie and get expected root
    updated_trie = StateTrie()
    expected_root, _ = updated_trie.merkelize(updated_vector)
    # print("expected root", expected_root)

    # Perform in-place update on the original trie
    new_root = trie.delete(keyval_to_delete[0])
    # print("new root", new_root)

    # The new root must equal the expected root
    assert new_root == expected_root
    assert trie.root_hash == expected_root
