import asyncio
from math import floor
from time import time

from jam.state.state import State
from jam.utils.constants import EPOCH_LENGTH
from jam.network.node import Node
from jam.config.logging import get_logger
from rockstore import RockStore
from jam.utils.dummy.dummy_package import create_dummy_package
from jam.network.protocols.ce_133 import WorkPackageSubmission, CE133Data
from jam.network.protocols.ce_133 import WorkPackageCore
from tsrkit_types.integers import Uint

# Module-specific logger
logger = get_logger("in_core")


async def wp_producer(node: Node, db: RockStore):
    """
    Continuously produces work packages and transmits them.
    A builder node produces a work package and share it with the guarantors.
    Args:
        node (Node): The network node for communications
        db (RockStore): The database to store the genesis timestamp
    """

    # Record genesis timestamp in seconds
    genesis_ts = time()
    C133 = WorkPackageSubmission()

    wp_iter = 0
    
    logger.info(
        "Starting work package producer",
        node_name=node.name,
        is_builder=node.is_builder,
        genesis_timestamp=genesis_ts
    )
    
    while True:
        if not node.is_initialized:
            logger.debug(
                "Network not initialized - skipping work package production",
                node_name=node.name,
                iteration=wp_iter
            )
            await asyncio.sleep(6)
            genesis_ts = time()
            continue

        # Get state from db
        state = State.load(db)
        current_timeslot = (time() - genesis_ts) // 6

        # Get current timeslot
        ts_epoch_index = floor(current_timeslot % EPOCH_LENGTH)

        logger.debug(
            "Work package production cycle",
            node_name=node.name,
            iteration=wp_iter,
            current_timeslot=current_timeslot,
            epoch_index=ts_epoch_index,
            gamma_mode=state.gamma.s.get_key()
        )

        if node.is_builder:
            wp = create_dummy_package()
            wc = WorkPackageCore(wp, Uint(0))
            data = CE133Data(package_data=wc, extrinsics=Uint(341))
            
            logger.info(
                "Producing work package",
                node_name=node.name,
                iteration=wp_iter,
                core_index=0,
                extrinsics_count=341,
                current_timeslot=current_timeslot
            )
            
            # TODO: Implement package transmission
            C133.transmit(node, data)
            
            logger.debug(
                "Work package transmitted",
                node_name=node.name,
                iteration=wp_iter
            )
        else:
            logger.debug(
                "Node is not builder - skipping work package production",
                node_name=node.name,
                iteration=wp_iter
            )

        # Sleep for remaining time of the timeslot
        await asyncio.sleep(6 - (time() - genesis_ts) % 6)
        wp_iter += 1