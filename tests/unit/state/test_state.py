import pytest
from coverage.annotate import os

from jam.block import Block
from jam.state.ghost import GhostState
from jam.state.state import setup_state, set_state
from jam.types import HeaderHash
from jam.utils.constants import GENESIS_HASH
from rockstore import RockStore
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32, U64
from jam.types.protocol.core import Balance, ServiceId, TimeSlot
from jam.types.protocol.crypto import Hash
from jam.types.state.delta import AccountData, LookupTable, Timestamps, AccountMetadata
from jam.types.state.tau import Tau
from jam.utils.dummy.utils import create_dummy_bytes
from jam.settings import setup_setting


def setup_genesis():
    from jam.finality.finality import Finality
    from jam.settings import settings

    block = Block.genesis()
    hh = block.save(settings.main_db)

    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    return hh

def test_state_sync(db_path):
    db = RockStore(db_path)
    setup_state(db, GhostState.genesis())
    from jam.state.state import state as updated_state

    assert updated_state.root != Bytes[32]([0] * 32)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_state_update(db_path, rpc):
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    state.tau = Tau(1)


    hh = setup_genesis()
    state.stash(hh)
    state.settle(hh)
    assert prev_hash != state.root

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_delta_update(db_path, rpc):
    settings = setup_setting(db_path, None, "alice", 0, rpc)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    state.delta[ServiceId(1)].service = AccountMetadata(
        code_hash=Bytes[32]([1] * 32),
        balance=U64(10000000),
        gas_limit=U64(10000000),
        min_gas=U64(10000000),
        num_o=U64(10000000),
        num_i=U32(100),
        gratis_offset=Balance(0),
        created_at=TimeSlot(0),
        accumulated_at=TimeSlot(0),
        parent_service=ServiceId(0),
    )

    hh = setup_genesis()
    state.stash(hh)
    state.settle(hh)

    assert prev_hash != state.root
    data_post = state.delta[ServiceId(1)].service
    assert data_post.code_hash == Bytes[32]([1] * 32)
    assert data_post.balance == U64(10000000)
    assert data_post.gas_limit == U64(10000000)
    assert data_post.min_gas == U64(10000000)
    assert data_post.num_o == U64(10000000)
    assert data_post.num_i == U32(100)
    assert data_post.gratis_offset == Balance(0)
    assert data_post.created_at == TimeSlot(0)
    assert data_post.accumulated_at == TimeSlot(0)
    assert data_post.parent_service == ServiceId(0)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_preimage_add(db_path, rpc):
    settings = setup_setting(db_path, None, "alice", 0, rpc)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] = Bytes(data)


    hh = setup_genesis()
    state.stash(hh)
    state.settle(hh)

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].preimages[Hash.blake2b(data)] == Bytes(data)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_storage_add(db_path, rpc):
    settings = setup_setting(db_path, None, "alice", 0, rpc)
    state = setup_state(settings.state_db, GhostState.genesis())
    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)] = AccountData()
    state.delta[ServiceId(1)].storage[Hash.blake2b(data)] = Bytes(data)


    hh = setup_genesis()
    state.stash(hh)
    state.settle(hh)

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].storage[Hash.blake2b(data)] == Bytes(data)

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_timestamps_add(db_path, rpc):
    settings = setup_setting(db_path, None, "alice", 0, rpc)
    state = setup_state(settings.state_db, GhostState.genesis())

    prev_hash = state.root
    data = create_dummy_bytes(100)
    state.delta[ServiceId(1)] = AccountData()
    state.delta[ServiceId(1)].lookup[LookupTable(hash=Hash.blake2b(data), length=100)] = Timestamps(
        []
    )


    hh = setup_genesis()
    state.stash(hh)
    state.settle(hh)

    assert prev_hash != state.root
    assert state.delta[ServiceId(1)].lookup[
        LookupTable(hash=Hash.blake2b(data), length=100)
    ] == Timestamps([])
