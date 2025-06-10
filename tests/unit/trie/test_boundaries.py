from tsrkit_types import ByteArray

from jam.state.merkle import StateTrie
from tsrkit_types.bytes import Bytes

from jam.utils.dummy.utils import create_dummy_bytes
from tests.unit.trie.visualise import visualize_trie

# Initial vector of key->value hex strings
vector = {
	Bytes[32].fromhex("d7f99b746f23411983df92806725af8e5cb66eba9f200737accae4a1ab7f47b9"): Bytes.fromhex(
		"24232437f5b3f2380ba9089bdbc45efaffbe386602cb1ecc2c17f1d0"),
	Bytes[32].fromhex("59ee947b94bcc05634d95efb474742f6cd6531766e44670ec987270a6b5a4211"): Bytes.fromhex(
		"72fdb0c99cf47feb85b2dad01ee163139ee6d34a8d893029a200aff76f4be5930b9000a1bbb2dc2b6c79f8f3c19906c94a3472349817af21181c3eef6b"),
	Bytes[32].fromhex("a3dc3bed1b0727caf428961bed11c9998ae2476d8a97fad203171b628363d9a2"): Bytes.fromhex("8a0dafa9d6ae6177"),
	Bytes[32].fromhex("15207c233b055f921701fc62b41a440d01dfa488016a97cc653a84afb5f94fd5"): Bytes.fromhex(
		"157b6c821169dacabcf26690df"),
	Bytes[32].fromhex("b05ff8a05bb23c0d7b177d47ce466ee58fd55c6a0351a3040cf3cbf5225aab19"): Bytes.fromhex("6a208734106f38b73880684b"),
	Bytes[32].fromhex("3dbc5f775f6156957139100c343bb5ae6589af7398db694ab6c60630a9ed0fcd"): Bytes(create_dummy_bytes(10)),
	Bytes[32].fromhex("5fd68f074c914741601931d64c6c772c18ab8a4cd0cd3a4fff0611a5d97ecc94"): Bytes(
		create_dummy_bytes(10)),
	Bytes[32].fromhex("d44438ec54b3f4d9771a43ed435f21b53a4f1f42be4c34b5d998bb9d53adc517"): Bytes(
		create_dummy_bytes(10)),
	Bytes[32].fromhex("d484d55a6f532466b844c01500e503cafad33b4f4f1493a2da0b3b1377bd383b"): Bytes(
		create_dummy_bytes(10)),
	Bytes[32].fromhex("ef11722d05e21b20e7a37e355c685df020a4dcf22fb888f10b0138c7cd162461"): Bytes(
		create_dummy_bytes(10)),
	Bytes[32].fromhex("f2a9fcaf8ae0ff770b0908ebdee1daf8457c0ef5e1106c89ad364236333c5fb3"): Bytes(
		create_dummy_bytes(10)),
}


def test_node_boundaries():
	"""Test that deleting a key in the trie produces the correct new root hash."""

	# Build original trie and get its root
	trie = StateTrie()
	root, _ = trie.merkelize(vector)
	print("\nTrie", visualize_trie(trie))

	boundaries = trie.get_boundaries(Bytes.fromhex("d44438ec54b3f4d9771a43ed435f21b53a4f1f42be4c34b5d998bb9d53adc517")[:31])
	assert len(boundaries) == 10

def test_node_not_found():
	# Build original trie and get its root
	trie = StateTrie()
	root, _ = trie.merkelize(vector)
	print("\nTrie", visualize_trie(trie))

	boundaries = trie.get_boundaries(
		Bytes.fromhex("d44438ec54b3f4d9771a43ed435f21b53a4f1f42be4c34b5d998bb9d53adc516")[:31])
	assert len(boundaries) == 10