import json
import os
from pathlib import Path

import pytest
from tsrkit_types import Bytes

from jam.finality.finality import Finality
from jam.state.state import State, setup_state
from jam.state.utils import construct_state_key
from jam.types import TimeSlot, HeaderHash, ServiceId, AccountData
from jam.utils.dummy.dummy_block import create_dummy_block
from jam.settings import setup_setting
from jam.block.block import Block
from tests.unit.api.utils import produce_chain


def get_gen_state(db_path):
    # Load genesis state
    genesis_path = Path(__file__).parents[3] / "dev-spec.json"
    settings = setup_setting(db_path, None)
    state = setup_state(settings.state_db, str(genesis_path))
    state.store.enable_cache()
    state.store.enable_writes()
    return state, settings


def test_state_update(db_path):
    state, _ = get_gen_state(db_path)

    # Make updates
    assert state.tau == 0
    state.tau += 1
    assert state.tau == 1

    # Ensure this is just added to cache and not to DB
    assert state.store._updates[construct_state_key(11)] == TimeSlot(1).encode()
    assert state.store.get(construct_state_key(11), skip_cache=True) == TimeSlot(0).encode()

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_block_import_state_save_n_fetch(db_path):
    state, setting = get_gen_state(db_path)
    db = setting.main_db

    parent = HeaderHash([0] * 32)
    for i in range(10):
        block = create_dummy_block()
        block.header.parent = parent
        block.header.slot = TimeSlot(i)

        # Mockup of state transition
        bh = HeaderHash(block.header.hash())
        state.tau = block.header.slot
        state.settle(bh)
        Finality.set_head(bh, db)

        block.save(db)

        # Parent for next blocks
        parent = bh

    hh_4 = db.get(Block.get_storage_key_slot(TimeSlot(4)))
    s_4 = state.load(hh_4)
    assert s_4.tau == TimeSlot(4)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_delta_updates(db_path):
    state, setting = get_gen_state(db_path)
    db = setting.main_db

    # Make updates
    state.delta[ServiceId(100)] = AccountData()
    assert state.delta[ServiceId(100)].service.code_hash == Bytes(32)

    state.delta[ServiceId(100)].service.code_hash = Bytes[32]([1] * 32)
    assert state.delta[ServiceId(100)].service.code_hash == Bytes([1] * 32)

    state.settle(HeaderHash([0] * 32))
