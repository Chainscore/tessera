import os
from pathlib import Path

import pytest
from tsrkit_types import Bytes

from jam.state.state import setup_state
from jam.state.utils import construct_state_key
from jam.models import TimeSlot, ServiceId, AccountData
from jam.settings import setup_setting
from jam.block.block import Block
from tests.unit.state.test_state_load import simulate_chain


def get_gen_state(db_path):
    # Load genesis state
    genesis_path = Path(__file__).parents[3] / "dev-spec.json"
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, str(genesis_path))
    state.store.enable_cache()
    state.store.enable_writes()
    return state, settings

# TODO: REGEN BLOCK VECTORS
# Skip legacy tests
@pytest.mark.asyncio
@pytest.mark.skip
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_state_update(db_path):
    state, _ = get_gen_state(db_path)

    # Make updates
    assert state.tau == 0
    state.tau += 1
    assert state.tau == 1

    # Ensure this is just added to cache and not to DB
    assert state.store._updates[construct_state_key(11)] == TimeSlot(1).encode()
    assert state.store.get(construct_state_key(11), skip_cache=True) == TimeSlot(0).encode()

@pytest.mark.asyncio
@pytest.mark.skip
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_block_import_state_save_n_fetch(db_path, rpc):
    vectors, settings = simulate_chain(db_path, rpc)
    from jam.state.state import state

    blocks_4 = Block.load_w_ts(TimeSlot(4), settings.main_db)
    assert len(blocks_4) == 1

    hh_4 = blocks_4[0].header.hash()
    assert hh_4 == vectors[4].header_hash
    assert blocks_4[0] == vectors[4].block

    s_4 = state.load(hh_4)
    assert s_4.tau == TimeSlot(4)


@pytest.mark.asyncio
@pytest.mark.skip
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_delta_updates(db_path, rpc):
    vectors, settings = simulate_chain(db_path, rpc)
    from jam.state.state import state

    hh = vectors[4].header_hash

    # Make updates
    state.delta[ServiceId(100)] = AccountData()
    assert state.delta[ServiceId(100)].service.code_hash == Bytes(32)

    state.delta[ServiceId(100)].service.code_hash = Bytes[32]([1] * 32)
    assert state.delta[ServiceId(100)].service.code_hash == Bytes([1] * 32)

    state.stash(hh)
    state.settle(hh)
