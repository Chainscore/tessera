from jam.state.ghost import GhostState
from jam.state.state import setup_state, set_state
from rockstore import RockStore
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32, U64
from jam.types.protocol.core import Balance, ServiceId
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountData, LookupTable, Timestamps, AccountMetadata
from jam.types.state.tau import Tau
from jam.utils.dummy.utils import create_dummy_bytes
from jam.settings import setup_setting 

def test_state_sync(db_path):
    db = RockStore(db_path)
    setup_state(db, GhostState.genesis())
    from jam.state.state import state as updated_state
    assert updated_state.root != Bytes[32]([0] * 32)

def test_state_update(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    state.tau = Tau(1)

    state.settle(header_hash=Bytes([1]*32))
    assert prev_hash != state.root

def test_delta_update(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    state.delta[ServiceId(1)].service = AccountMetadata(
        code_hash=Bytes[32]([1] * 32),
        balance=U64(10000000),
        gas_limit=U64(10000000),
        min_gas=U64(10000000),
        num_o=U64(10000000),
        num_i=U32(100),
    )
    state.settle(header_hash=Bytes([1]*32))

    assert prev_hash != state.root
    data_post = state.delta[ServiceId(1)].service
    assert data_post.code_hash == Bytes[32]([1] * 32)
    assert data_post.balance == U64(10000000)
    assert data_post.gas_limit == U64(10000000)
    assert data_post.min_gas == U64(10000000)
    assert data_post.num_o == U64(10000000)
    assert data_post.num_i == U32(100)

def test_preimage_add(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] = Bytes(data)

    state.settle(header_hash=Bytes([1]*32))

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] == Bytes(data)

def test_storage_add(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)] = AccountData()
    state.delta[ServiceId(1)].storage[Hash.blake2b(data)] = Bytes(data)

    state.settle(header_hash=Bytes([1]*32))

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].storage[Hash.blake2b(data)] == Bytes(data)

def test_timestamps_add(db_path):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())

    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)] = AccountData()
    state.delta[ServiceId(1)].lookup[LookupTable(hash=Hash.blake2b(data), length=100)] = Timestamps([])

    state.settle(header_hash=Bytes([1]*32))

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].lookup[LookupTable(hash=Hash.blake2b(data), length=100)] == Timestamps([])
