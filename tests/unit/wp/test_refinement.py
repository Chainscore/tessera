import asyncio
import json
from time import time
from typing import cast

import pytest
import os

from tsrkit_types import U32

from jam.logging import get_logger
from jam.network.protocols import WorkPackageSubmission
from jam.network.protocols.ce_133 import CE133Data, WorkPackageCore
from jam.types import Hash
from jam.utils.constants import GENESIS_TS
from jam.storage.da.mappings import (
    PackageSegmentMap,
    SegmentErasureMap,
)
from jam.storage.da.reports import ReportsDA
from tests.integration.utils.setup_processes import Client, Role, setup_processes
from tests.unit.wp.types import RefineVectors, RefineVector, BundleVector, BundleVectors

# Logger for WP Production
# logger = get_logger("test")

CLIENTS = [
    Client(Role.VAL, 40000, theme="cyberpunk"),
    Client(Role.VAL, 40001, theme="monokai"),
    Client(Role.VAL, 40002, theme="noir"),
    Client(Role.VAL, 40003, theme="sunset"),
    Client(Role.VAL, 40004, theme="gruvbox"),
    Client(Role.VAL, 40005, theme="dracula"),
    Client(Role.BUILDER, 40006, theme="nord"),
]

vectors = BundleVectors([])
for i in range(1, 4):
    with open(f"vectors/bundles/bundles-{i:03d}.json", "r") as f:
        data = json.load(f)
        bundle_vec = BundleVector.from_json(data)
        vectors.append(bundle_vec)


async def node_task():
    # Wait for initialization
    await asyncio.sleep(12)

    init_ts = int((time() - GENESIS_TS) // 6)

    from jam.network.node import node

    if node.is_builder:
        logger = get_logger()

        ts = init_ts

        CE133 = WorkPackageSubmission()
        for wp_iter, vector in enumerate(vectors):
            try:
                wpc = WorkPackageCore(vector.work_package, vector.core_index)
                wp_len = U32(len(wpc.encode()))
                ext = vector.extrinsics
                ext_len = U32(len(ext.encode()))
                wp_data = CE133Data(wp_len, wpc, ext_len, ext)

                acks = await CE133.transmit(node, wp_data)

                logger.info(
                    "Testing builder transmission",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    peers=len(node.peer_conn),
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
    else:
        await asyncio.sleep(20)
        from jam.settings import settings

        logger = get_logger()

        d3l = settings.d3l

        logger.info("VALIDATOR NODE", node=node)

        for wp_iter, vector in enumerate(vectors):
            try:
                rep_da = ReportsDA(d3l)
                map_da = PackageSegmentMap(d3l)
                sr_er_da = SegmentErasureMap(d3l)

                wr = rep_da.get(vector.rep_hash)
                logger.debug("WORK REP", assertion=wr == vector.work_rep)
                assert wr.encode() == vector.work_rep.encode()

                wp_hash = Hash.blake2b(vector.work_package.encode())
                sr = map_da.get(wp_hash)
                logger.debug(
                    "SEG ROOT",
                    assertion=sr == vector.work_rep.package_spec.exports_root,
                )
                assert sr.encode() == vector.work_rep.package_spec.exports_root.encode()

                er = sr_er_da.get(sr)
                logger.debug(
                    "ERS ROOT",
                    assertion=er == vector.work_rep.package_spec.erasure_root,
                    exp=vector.work_rep.package_spec.erasure_root.hex(),
                    got=er.hex(),
                )
                assert er.encode() == vector.work_rep.package_spec.erasure_root.encode()

                logger.info(
                    "Node assertion successful",
                    peers=len(node.peer_conn),
                )
            except Exception as e:
                logger.error(
                    "Error occurred while testing node assertion",
                    err=str(e),
                    err_type=type(e).__name__,
                )


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_refinement():
    await setup_processes(CLIENTS, node_task, 36)
