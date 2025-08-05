import json
import time
from copy import deepcopy

from jam.block import Block, GuaranteesExtrinsic
from jam.state.ghost import GhostState
from jam.types import TimeSlot
from jam.utils.constants import GENESIS_TS, SLOT_PERIOD
from tests.unit.incore.types import BundleVectors, BundleVector

vectors = BundleVectors([])
for i in range(0, 100):
    with open(f"vectors/bundles/bundles-{i:03d}.json", "r") as f:
        data = json.load(f)
        bundle_vec = BundleVector.from_json(data)
        vectors.append(bundle_vec)



async def test_vectorize():
    curr_ts = int((time.time() - GENESIS_TS) // SLOT_PERIOD)
    ts = curr_ts

    while ts - curr_ts < 50:
        from jam.state.state import state
        pre_state = deepcopy(state)

        block = Block().produce(TimeSlot(ts), None)
        block.extrinsic.guarantees = GuaranteesExtrinsic([])
        state.transition(block)







        
        ts += 1