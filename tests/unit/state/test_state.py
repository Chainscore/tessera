from jam.config.data_stores import main_db
from jam.state.ghost import GhostState
from jam.state.state import setup_state, set_state
from jam.storage.db.kv import KVStore
from jam.types.base import ByteArray32, U64, U32, Bytes
from jam.types.protocol.core import Balance, ServiceId
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountData, LookupTable, Timestamps, AccountMetadata
from jam.types.state.tau import Tau
from jam.utils.dummy.utils import create_dummy_bytes

state = setup_state(GhostState.genesis(), main_db)

def test_state_sync(db_path):
    db = KVStore(db_path)
    setup_state(GhostState.genesis(), db)
    from jam.state.state import state as updated_state
    assert updated_state.TRIE.root_hash != ByteArray32([0] * 32)

def test_state_update():
    prev_hash = state.TRIE.root_hash
    state.tau = Tau(1)
    assert prev_hash != state.TRIE.root_hash

def test_delta_update():
    prev_hash = state.TRIE.root_hash
    state.delta[ServiceId(1)].service = AccountMetadata(
        code_hash=ByteArray32([1] * 32),
        balance=U64(10000000),
        gas_limit=U64(10000000),
        min_gas=U64(10000000),
        num_o=U64(10000000),
        num_i=U32(100),
    )
    assert prev_hash != state.TRIE.root_hash
    data_post = state.delta[ServiceId(1)].service
    assert data_post.code_hash == ByteArray32([1] * 32)
    assert data_post.balance == U64(10000000)
    assert data_post.gas_limit == U64(10000000)
    assert data_post.min_gas == U64(10000000)
    assert data_post.num_o == U64(10000000)
    assert data_post.num_i == U32(100)

def test_preimage_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] = Bytes(data)
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] == Bytes(data)

def test_storage_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].storage[Hash.blake2b(data)] = Bytes(data)
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].storage[Hash.blake2b(data)] == Bytes(data)

def test_timestamps_add():
    prev_hash = state.TRIE.root_hash
    data = create_dummy_bytes(100)

    state.delta[ServiceId(1)].lookup[LookupTable(hash=Hash.blake2b(data), length=100)] = Timestamps([])
    assert prev_hash != state.TRIE.root_hash
    assert state.delta[ServiceId(1)].lookup[LookupTable(hash=Hash.blake2b(data), length=100)] == Timestamps([])

