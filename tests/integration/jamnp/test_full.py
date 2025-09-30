import asyncio
import json
from time import time
from typing import cast

import pytest
import os

from tsrkit_types import U32, Null

from jam.block import Block
from jam.log_setup import node_logger as logger
from jam.network.protocols import WorkPackageSubmission
from jam.network.protocols.ce_133 import CE133Data, WorkPackageCore
from jam.operations import operate
from jam.types import Hash, WorkPackage, RefineContext, BeefyRoot, HeaderHash
from jam.types.state.beta import BlockHistory
from jam.utils.constants import GENESIS_TS
from tests.integration.jamnp.utils.fetch_test_vectors import fetch_vectors

from tests.integration.utils.setup_processes import Client, Role, setup_processes
from tests.unit.incore.types import BundleVector, BundleVectors, BlockVector, FullVector, FullVectors, BlockVectors

CLIENTS = [
    Client(Role.VAL, 40000, theme="forest"),
    Client(Role.VAL, 40001, theme="ocean"),
    Client(Role.VAL, 40002, theme="retro"),
    Client(Role.VAL, 40003, theme="sunset"),
    Client(Role.VAL, 40004, theme="gruvbox"),
    Client(Role.VAL, 40005, theme="dracula"),
    # Client(Role.BUILDER, 40006, theme="nord"),
]

vectors = BundleVectors([])
# fetch_vectors(1, 12, vectors)
b_vectors = BlockVectors([])

async def node_task():
    # Wait for initialization
    await asyncio.sleep(14)
    CE133 = WorkPackageSubmission()

    init_ts = int((time() - GENESIS_TS) // 6)

    from jam.finality.finality import Finality
    from jam.network.start import node
    from jam.settings import settings
    from jam.utils.merkle.mountain_merkle import MMRFunctions

    wp_iter = 0
    while wp_iter < len(vectors):

        settings.update()
        if node.port == 40004:
            vector = vectors[wp_iter]
            merklizer = MMRFunctions()

            ts = init_ts

            try:
                from jam.state.state import state

                wp: WorkPackage = vector.work_package
                if len(state.beta):
                    lookup_anchor: Block = Finality.load_final(settings.main_db)
                    last_block: Block = Finality.load_latest(settings.main_db)
                    anchor: BlockHistory = state.beta[-1]
                    refine_context = RefineContext.empty()

                    refine_context.anchor = anchor.header_hash
                    refine_context.state_root = state.root
                    refine_context.beefy_root = BeefyRoot(merklizer.super_peak(anchor.mmr))
                    # refine_context.lookup_anchor = HeaderHash(lookup_anchor.header.hash())
                    # refine_context.lookup_anchor_slot = lookup_anchor.header.slot

                    refine_context.lookup_anchor = HeaderHash(last_block.header.hash())
                    refine_context.lookup_anchor_slot = last_block.header.slot
                    wp.context = refine_context
                    logger.info("OVERRIDDEN REFINE CONTEXT", context=refine_context.to_json())

                wpc = WorkPackageCore(wp, vector.core_index)
                wp_len = U32(len(wpc.encode()))
                ext = vector.extrinsics
                ext_len = U32(len(ext.encode()))
                wp_data = CE133Data(wp_len, wpc, ext_len, ext)

                if state.rho[vector.core_index].unwrap() != Null:
                    logger.debug("CORE ENGAGED, SLEEPING", wp_iter=wp_iter)
                    await asyncio.sleep(6)
                    continue
                acks = await CE133.transmit(wp_data)

                logger.info(
                    "Transmitted work package",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    peers=node.all_connected,
                )

            except Exception as e:
                logger.error(
                    "Error occurred while testing builder",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    err=str(e),
                    err_type=type(e).__name__,
                )
            finally:
                ts += 1

            await asyncio.sleep(6)

        wp_iter += 1


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_full_vectorize():
    await setup_processes(CLIENTS, [node_task, operate], 140)
