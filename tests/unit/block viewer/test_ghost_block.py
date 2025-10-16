import os
import pytest



from tsrkit_types import Dictionary, Enum, structure, Option, TypedVector, Null
from tests.unit.state.test_state_load import simulate_chain


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_load_final(db_path, rpc):
    vectors, settings = simulate_chain(db_path, rpc)
    from jam.block.block_view import viewer
    print("\n\nFINAL TREEE\n\n")
    viewer.visualize()

