import asyncio
from time import time

from jam.config.logging import logger
from jam.utils.dummy.utils import create_dummy_bytes32
from jam.network.node import Node
from jam.storage.db.kv import KVStore
from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data

async def work_report_request_producer(node: Node, db: KVStore):
    """
    Continuously simulates requesting missing work-reports by hash.
    This can be triggered on block reception (here, simulated in a loop).

    Args:
        node (Node): The network node for communications
        db (KVStore): The database instance
    """

    RequestProtocol = WorkReportRequest()

    request_iter = 0
    while True:
        if not node.is_initialized:
            logger.info(f"🔄 ({node.name}) Network not initialized, skipping work-report requests")
            await asyncio.sleep(6)
            continue

        # Simulate a missing work-report hash
        missing_hash = f"dummy_hash_{request_iter}"

        logger.info(f"📨 ({node.name}) Requesting Work-Report with hash {missing_hash}")

        # Select a target peer node (could be node.peers[0] in real)
        if not node.peers:
            logger.info(f"⚠️ ({node.name}) No peers connected, skipping request")
        else:
            request_data = CE136Data(work_report_hash=create_dummy_bytes32())

            # Send request via CE 136 protocol
            RequestProtocol.transmit(node, request_data)

        await asyncio.sleep(6)
        request_iter += 1
