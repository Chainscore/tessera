import os
from pathlib import Path

import pytest
from jam.settings import setup_setting
from jam.state.state import setup_state
from jam.block import Block
from jam.types.protocol.core import TimeSlot
from jam.finality.finality import Finality

@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_block_production(db_path):
    genesis_path = Path(__file__).parents[3] / "dev-spec.json"
    settings = setup_setting(db_path, 0, "alice", 3000)
    state = setup_state(settings.state_db, str(genesis_path))

    block_0 = Block.genesis()
    hh_0 = block_0.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh_0, settings.main_db)
    Finality.set_head(hh_0, settings.main_db)

    genesis = Block.load_w_ts(TimeSlot(0), settings.main_db)
    assert genesis is not None
    with pytest.raises(ValueError):
        Block.load_w_ts(TimeSlot(1), settings.main_db)

    # First block production
    block_1 = genesis.produce(TimeSlot(1))
    assert block_1.header.slot == TimeSlot(1)
    block_1.save(settings.main_db)
    assert Block.load_w_ts(TimeSlot(1), settings.main_db) == block_1
    with pytest.raises(ValueError):
        Block.load_w_ts(TimeSlot(2), settings.main_db)

    # Second block
    settings.clear()

    settings = setup_setting(db_path, 3, "dave", 3000)
    state = setup_state(settings.state_db)

    block_2 = block_1.produce(TimeSlot(2))
    assert block_2.header.slot == TimeSlot(2)
    block_2.save(settings.main_db)
    assert Block.load_w_ts(TimeSlot(2), settings.main_db) == block_2
    assert block_2.load_parent(settings.main_db) == block_1

    # Finality
    Finality.set_head(block_1.header.hash(), settings.main_db)
    Finality.set_head(block_2.header.hash(), settings.main_db)
    Finality.finalise(block_1.header.hash(), settings.main_db)

    assert Finality.load_final(settings.main_db) == block_1
    latest = Finality.load_latest(settings.main_db)
    assert Finality.load_latest(settings.main_db) == block_2
