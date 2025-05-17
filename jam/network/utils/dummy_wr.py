import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.network.node import Node
from jam.config.logging import logger
from jam.db.kv import KVStore
from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data
from jam.types.protocol.core import TimeSlot


async def work_report_producer(node: Node, db: KVStore):
    """
    Continuously produces work reports and transmits them.
    A builder node generates a report and shares it with the network.

    Args:
        node (Node): The network node for communications
        db (KVStore): The database to store the genesis timestamp
    """

    genesis_ts = time()
    ReportProtocol = WorkReportDistribution()

    report_iter = 0
    while True:
        print("time", genesis_ts, time())

        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network is not initialized, skipping report production")
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.info(f"We're in epoch slot {ts_epoch_index} and {state.gamma.s.get_key()} mode")

        if not node.is_builder:
            report = create_dummy_work_report()
            report_data = CE135Data(report=report, slot=TimeSlot(int(current_timeslot)))

            logger.info(f"📝 ({node.name}) Producing Work Report {report_iter}")

            ReportProtocol.transmit(node, report_data)
        else:
            logger.info(f"🔄 ({node.name}) skipping Node")

        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        report_iter += 1
