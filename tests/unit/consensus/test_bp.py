import os

import pytest
from jam.consensus.bp_engine import BlockProducer
from rockstore import RockStore
from jam.network.node import Node
from jam.state.ghost import GhostState as State
from jam.types.block import Block
from jam.types.protocol.core import TimeSlot
from jam.consensus.grandpa.finality import Finality


@pytest.mark.skip("This is work in progress")
def test_block_production(db_path):
    db = RockStore(db_path)
    state = State.genesis()
    os.environ["SEED"] = "1"
    node = Node("test_node", "0.0.0.0", 30333, state.kappa[0], [], False, True)
    producer = BlockProducer(node, db)
    genesis = Block.load(TimeSlot(0), db)
    assert genesis == Block.genesis()
    with pytest.raises(ValueError):
        Block.load(TimeSlot(1), db)
    # First block production
    block_1 = producer._produce_block(state, TimeSlot(1))
    assert block_1.header.slot == TimeSlot(1)
    block_1.save(db)
    assert Block.load(TimeSlot(1), db) == block_1
    with pytest.raises(ValueError):
        Block.load(TimeSlot(2), db)
    #second block
    block_2 = producer._produce_block(state, TimeSlot(2))
    assert block_2.header.slot == TimeSlot(2)
    block_2.save(db)
    assert Block.load(TimeSlot(2), db) == block_2
    assert Block.load_parent(TimeSlot(2), db) == block_1

    # Finality
    Finality.set_head(block_2.header.slot, db)
    Finality.finalise(block_1.header.slot, db)

    assert Finality.load_final(db) == block_1
    assert Finality.load_latest(db) == block_2