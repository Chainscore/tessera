import asyncio

from jam.logging import get_logger
from jam.utils.dummy.utils import create_dummy_bytes32
from jam.network.node import Node
from rockstore import RockStore
from jam.network.protocols.ce_136 import WorkReportRequest, CE136Data

# Module-specific logger
logger = get_logger("in_core")

async def work_report_request_producer(node: Node, db: RockStore):
    """
    Continuously simulates requesting missing work-reports by hash.
    This can be triggered on block reception (here, simulated in a loop).

    Args:
        node (Node): The network node for communications
        db (RockStore): The database instance
    """

    RequestProtocol = WorkReportRequest()

    request_iter = 0
    
    logger.info(
        "Starting work report request producer",
        node_name=node.name,
        peer_count=len(node.peers)
    )
    
    while True:
        if not node.is_initialized:
            logger.debug(
                "Network not initialized - skipping work report requests",
                node_name=node.name,
                iteration=request_iter
            )
            await asyncio.sleep(6)
            continue

        # Simulate a missing work-report hash
        missing_hash = create_dummy_bytes32()

        logger.info(
            "Requesting missing work report",
            node_name=node.name,
            iteration=request_iter,
            work_report_hash=missing_hash.hex()[:16] + "..."
        )

        # Select a target peer node (could be node.peers[0] in real)
        if not node.peers:
            logger.warning(
                "No peers available for work report request",
                node_name=node.name,
                iteration=request_iter
            )
        else:
            request_data = CE136Data(work_report_hash=missing_hash)

            # Send request via CE 136 protocol
            RequestProtocol.transmit(node, request_data)
            
            logger.debug(
                "Work report request transmitted",
                node_name=node.name,
                iteration=request_iter,
                target_peers=len(node.connections)
            )

        await asyncio.sleep(6)
        request_iter += 1
