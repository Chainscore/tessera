from jam.storage.db.kv import KVStore
from jam.state.accounts import AccountData
from jam.state.ghost import GhostState
from jam.state.state import setup_state, state
from jam.types import ByteArray32, ServiceId, U64, U32, Bytes
from jam.types.protocol.core import Balance
from jam.types.protocol.crypto import Hash
from jam.types.state import Eta, Tau, LookupTimestamps, LookupTable, Timestamps
from tests.dummy.utils import create_dummy_bytes


def test_state_sync(db_path):
    db = KVStore(db_path)
    assert state.TRIE.root_hash == ByteArray32([0] * 32)
    setup_state(GhostState.genesis(), db)
    from jam.state.state import state as updated_state
    assert updated_state.TRIE.root_hash != ByteArray32([0] * 32)

def test_state_update():
    prev_hash = state.TRIE.root_hash
    state.tau = Tau(1)
    assert prev_hash != state.TRIE.root_hash

def test_delta_update():
    prev_hash = state.TRIE.root_hash
    state.delta[ServiceId(1)] = AccountData(
        code_hash=ByteArray32([1] * 32),
        balance=U64(10000000),
        gas_limit=U64(10000000),
        min_gas=U64(10000000),
        num_o=U64(10000000),
        num_i=U32(100),
    )
    assert prev_hash != state.TRIE.root_hash
    data_post = state.delta[ServiceId(1)]
    assert data_post.code_hash == ByteArray32([1] * 32)
    assert data_post.balance == U64(10000000)
    assert data_post.gas_limit == U64(10000000)
    assert data_post.min_gas == U64(10000000)
    assert data_post.num_o == U64(10000000)
    assert data_post.num_i == U32(100)

def test_preimage_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].lookup[Hash.blake2b(data)] = Bytes(data)
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].lookup[Hash.blake2b(data)] == Bytes(data)

def test_storage_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].storage[Hash.blake2b(data)] = Bytes(data)
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].storage[Hash.blake2b(data)] == Bytes(data)

def test_timestamps_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)

    state.delta[ServiceId(1)].timestamps[LookupTable(hash=Hash.blake2b(data), length=100)] = Timestamps([])
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].timestamps[LookupTable(hash=Hash.blake2b(data), length=100)] == Timestamps([])

