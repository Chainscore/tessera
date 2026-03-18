import pytest

pytestmark = pytest.mark.unit

from copy import deepcopy
from tsrkit_types import Bytes
from jam.utils.trie.merkle import StateTrie
from tests.unit.trie.visualise import visualize_trie


def test_trace_test():
    initial = {}
    updates = [
        [
            "00ff00ff00ff00fffd520ac77481bdd497a893ab9d59b6fe450780a08dac5b",
            "fadd2180bd6b1cfa73a67e7892d878521ef69918995040fb8661647d321e0c55",
        ],
        [
            "00ff00ff00ff00fffd520ac77481bdd497a893ab9d59b6fe450780a08dac5b",
            "fadd2180bd6b1cfa73a67e7892d878521ef69918995040fb8661647d321e0c55",
        ],
        [
            "ff000000000000000000000000000000000000000000000000000000000000",
            "395be3f4f9749460400badafee623f5b5f9ecab34f4f65483c62e62eab147281ffffffffffffffff0a000000000000000a00000000000000ff790200000000000e000000",
        ],
    ]
    # Merklize pre_state + add updates = root1
    trie1 = StateTrie()
    trie1.merkelize(initial)
    for update in updates:
        trie1.update(Bytes.fromhex(update[0]), Bytes.fromhex(update[1]))
    # print(visualize_trie(trie1))

    # Have prestate, override keys with updates, merklize = root2
    fulldata = deepcopy(initial)
    for update in updates:
        fulldata[Bytes.fromhex(update[0])] = Bytes.fromhex(update[1])
    trie2 = StateTrie()
    trie2.merkelize(fulldata)
    # print(visualize_trie(trie2))

    assert trie1.root_hash.hex() == trie2.root_hash.hex()
