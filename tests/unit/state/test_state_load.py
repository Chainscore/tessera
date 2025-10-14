import os
import json
from pathlib import Path

import pytest

from jam.finality.finality import Finality

from tests.unit.api.utils import Vectors
from tsrkit_types import TypedVector, structure


FINALIZED_BLOCK = 3

def simulate_chain(db_path, rpc: bool = True):
    """
    Produce chain of 5 blocks and save in db.
    Returns states and blocks instances.
    """
    from jam.state.state import setup_state
    from jam.settings import setup_setting

    genesis_path = Path(__file__).parents[3] / "dev-spec.json"
    vectors_path = Path(__file__).parent / "blocks.json"
    settings = setup_setting(db_path, 0, "alice", 3000, rpc)
    state = setup_state(settings.state_db, str(genesis_path))

    with open(vectors_path, "r") as f:
        data = json.load(f)
        vectors = Vectors.from_json(data)

    for i in range(6):
        state_root = vectors[i].state_root
        block = vectors[i].block
        header_hash = vectors[i].header_hash

        if i == 0:
            hh = block.save(settings.main_db)  # Save to test-specific DB
            assert hh == header_hash
            assert state.root == state_root
            Finality.set_head(block, settings.main_db)
            Finality.finalise(block, settings.main_db)

            continue

        state._force_transition(block, i <= FINALIZED_BLOCK)

    return vectors, settings


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_load_final(db_path, rpc):
    from jam.finality.finality import Finality
    from jam.state.state import State

    vectors, settings = simulate_chain(db_path, rpc)

    fb = Finality.load_final(settings.main_db)
    assert fb.header.hash() == vectors[FINALIZED_BLOCK].header_hash

    fs = State.load(vectors[FINALIZED_BLOCK].header_hash)
    assert fs.root == vectors[FINALIZED_BLOCK].state_root


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_load_pre_final(db_path, rpc):
    from jam.state.state import State

    vectors, settings = simulate_chain(db_path, rpc)
    pb = vectors[1]

    s = State.load(pb.header_hash)
    assert s.root == pb.state_root

    pb = vectors[2]

    s = State.load(pb.header_hash)
    assert s.root == pb.state_root


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_load_post_final(db_path, rpc):
    from jam.state.state import State

    vectors, settings = simulate_chain(db_path, rpc)
    pb = vectors[4]

    s = State.load(pb.header_hash)
    assert s.root == pb.state_root

    pb = vectors[5]

    s = State.load(pb.header_hash)
    assert s.root == pb.state_root