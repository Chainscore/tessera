import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from jam.utils.dummy.dummy_extrinsics import create_dummy_work_report
from jam.network.node import Node
from jam.logging import pvm_logger
from rockstore import RockStore
from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data
from jam.types.protocol.core import TimeSlot

# Module-specific logger
logger = pvm_logger


async def work_report_producer(node: Node, db: RockStore):
    """
    Continuously produces work reports and transmits them.
    A builder node generates a report and shares it with the network.

    Args:
        node (Node): The network node for communications
        db (RockStore): The database to store the genesis timestamp
    """

    genesis_ts = time()
    ReportProtocol = WorkReportDistribution()

    report_iter = 0

    logger.info(
        "Starting work report producer",
        node_name=node.name,
        is_builder=node.is_builder,
        genesis_timestamp=genesis_ts,
    )

    while True:
        if not node.is_initialized:
            logger.debug(
                "Network not initialized - skipping work report production",
                node_name=node.name,
                iteration=report_iter,
            )
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.debug(
            "Work report production cycle",
            node_name=node.name,
            iteration=report_iter,
            current_timeslot=current_timeslot,
            epoch_index=ts_epoch_index,
            gamma_mode=state.gamma.s.get_key(),
        )

        if not node.is_validator:
            report = create_dummy_work_report()
            report_data = CE135Data(report=report, slot=TimeSlot(int(current_timeslot)))

            logger.info(
                "Producing work report",
                node_name=node.name,
                iteration=report_iter,
                current_timeslot=current_timeslot,
                core_index=int(report.core_index),
            )

            ReportProtocol.transmit(report_data)

            logger.debug(
                "Work report transmitted",
                node_name=node.name,
                iteration=report_iter,
                core_index=int(report.core_index),
            )
        else:
            logger.debug(
                "Node is builder - skipping work report production",
                node_name=node.name,
                iteration=report_iter,
            )

        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        report_iter += 1
