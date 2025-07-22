from jam.block.block import Block
from jam.finality.finality import Finality
from jam.settings import setup_setting
from jam.state.state import setup_state
from jam.types.protocol.core import TimeSlot


def test_block_production(db_path):
    settings = setup_setting(db_path, 0, "alice", 0)
    state = setup_state(settings.state_db)

    block = Block.genesis()
    hh = block.save(settings.main_db)  # Save to test-specific DB
    Finality.finalise(hh, settings.main_db)
    Finality.set_head(hh, settings.main_db)

    b = block.produce(TimeSlot(1))
    assert b.validate()
    state.transition(b)

    for i in range(2, 100):
        b = b.produce(TimeSlot(i))
        assert b.validate()
        state.transition(b)
        print("✅")
