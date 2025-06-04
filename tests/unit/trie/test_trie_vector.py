import json
from pathlib import Path
from jam.state.merkle.merkle import StateTrie
from tsrkit_types.bytes import Bytes


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
        state_dict = {Bytes[32].fromhex(k): Bytes(v) for k, v in vector["input"].items()}
        root,_ = trie.merkelize(state_dict)
        assert root == Bytes[32].fromhex(vector["output"])
        print(f"✅ Passed vector #{v_index} - Root = {root}")
