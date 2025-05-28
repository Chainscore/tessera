import json
from pathlib import Path
from jam.state.merkle.merkle import StateTrie
from jam.types.base.bytes.byte_array import ByteArray32
from jam.types.base.bytes.bytes import Bytes


def test_trie_vector():
    """Test that the trie vector is encoded and decoded correctly."""
    test_dir = Path(__file__).parent

    # Load test vectors
    with open(test_dir / "trie.json", "r") as f:
        vectors_json = json.load(f)

    trie = StateTrie()
    for v_index, vector in enumerate(vectors_json):
        # Construct a dictionary from the input
        print(f"Testing vector #{v_index}")
        state_dict = {ByteArray32(k): Bytes(v) for k, v in vector["input"].items()}
        root,_ = trie.merkelize(state_dict)
        assert root == ByteArray32(vector["output"])
        print(f"✅ Passed vector #{v_index} - Root = {root}")
