import asyncio
from math import floor
from time import time

from jam.network.protocols.ce_140 import SegmentShardRequestWithJustifications
from jam.network.protocols.ce_139_base import ShardRequest, SegmentIndexes, CE139Data
from jam.network.protocols.ce_139 import SegmentShardRequest
from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from tests.dummy.dummy_extrinsics import create_dummy_work_report
from jam.network.node import Node
from jam.logging import logger
from jam.storage.db.kv import KVStore
from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data
from jam.types.protocol.core import TimeSlot
from tests.dummy.utils import create_dummy_bytes32, create_dummy_bytes12
from jam.types.base.integers.fixed import U16
from jam.types.base.integers.general import Int


def create_dummy_segment_shard() -> ShardRequest:
    return ShardRequest(
        erasure_root=create_dummy_bytes32(),
        shard_Index=U16(1),
        length=Int(2),
        seg_indexes=SegmentIndexes([Int(2), Int(3)]),
    )


async def segment_shard_request(node: Node, db: KVStore):
    genesis_ts = time()
    shard_req = SegmentShardRequestWithJustifications()

    report_iter = 0
    while True:
        print("time in segment shard protocol")

        if not node.is_initialized:
            logger.info(
                f"🔄 ({node.name}) Network is not initialized, skipping segment shard request"
            )
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        if node.is_validator:
            print("inside the ce139")
            shard_request = create_dummy_segment_shard()
            shard_data: CE139Data = CE139Data([shard_request])

            print("shard data", shard_data)

            shard_req.transmit(node, shard_data)
        else:
            print("skipping in segment shard")
            logger.info(f"🔄 ({node.name}) skipping Node")

        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        report_iter += 1
