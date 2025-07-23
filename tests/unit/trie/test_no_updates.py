import json
from pathlib import Path

from tsrkit_types import Bytes

from jam.utils.trie.merkle import StateTrie
from tests.unit.trie.visualise import visualize_trie


def test_no_updates():
    tree_data = json.load(open(Path(__file__).parents[3] / "dev-spec.json"))["genesis_state"]
    trie = StateTrie()
    assert trie.root_hash == bytes(32)
    data_ = {Bytes.fromhex(k): Bytes.fromhex(v) for k, v in tree_data.items()}
    trie.merkelize(data_)
    root = trie.root_hash

    for _ in range(10):
        for k, v in data_.items():
            assert trie.update(k, v) == root 

def test_pj_testcase():
    tree_data = json.load(open(Path(__file__).parents[3] / "dev-spec.json"))["genesis_state"]
    trie = StateTrie()
    assert trie.root_hash == bytes(32)
    data_ = {Bytes.fromhex(k): Bytes.fromhex(v) for k, v in tree_data.items()}
    trie.merkelize(data_)

    print(visualize_trie(trie))

    fed8 = json.load(open(Path(__file__).parents[3] / "state_updates_3654.json"))

    for k, v in fed8.items():
        trie.update(Bytes.fromhex(k), Bytes.fromhex(v)) 
    
    expected = "d9df23282a5b0452bf82e365b6ca4532cbe0730a5d5668b112e00bd858ac07e1"
    assert trie.root_hash.hex() == expected

    # actual = "3009ad069cf09cf88af594a24c92010eed9ba76016a447b01eb8b18550053778' 
