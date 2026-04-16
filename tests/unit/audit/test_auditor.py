import asyncio
import json
from time import time

import pytest
import os

from tsrkit_types import U32

from jam.audit.assembler import Assembler
from jam.incore.processor import Processor
from jam.log_setup import node_logger as logger
from jam.network.protocols import WorkPackageSubmission
from jam.network.protocols.ce_133 import CE133Data, WorkPackageCore
from jam.models import Hash
from jam.utils.constants import GENESIS_TS
from jam.storage.da.mappings import (
    PackageSegmentMap,
    SegmentErasureMap,
)
from jam.storage.da.reports import ReportsDA
from tests.integration.jamnp.utils.fetch_test_vectors import fetch_vectors
from tests.integration.utils.setup_processes import Client, Role, setup_processes
from tests.unit.incore.types import RefineVectors, RefineVector, BundleVector, BundleVectors


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
# fetch_vectors(14, 24, vectors)


async def node_task():

    # Wait for initialization
    logger.debug("GOING TO SLEEP", timeout=6)
    await asyncio.sleep(6)
    init_ts = int((time() - GENESIS_TS) // 6)
    logger.debug("WAKING UP", ts=init_ts)


    from jam.network.start import node

    if node.is_builder:
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

            ts += 1

            # await asyncio.sleep(6)
    elif node.port == 40004:
        await asyncio.sleep(12)
        from jam.settings import settings

        d3l = settings.d3l

        logger.info("AUDITOR NODE", node=node)

        assembler = Assembler()
        processor = Processor()

        for wp_iter, vector in enumerate(vectors):
            try:
                rep_da = ReportsDA(d3l)
                map_da = PackageSegmentMap(d3l)
                sr_er_da = SegmentErasureMap(d3l)

                wr = rep_da.get(vector.rep_hash)
                assert wr == vector.work_rep

                wp_hash = Hash.blake2b(vector.work_package.encode())
                sr = map_da.get(wp_hash)
                assert sr == vector.work_rep.package_spec.exports_root

                er = sr_er_da.get(sr)
                assert er == vector.work_rep.package_spec.erasure_root

                logger.debug(
                    "Node assertion successful",
                    peers=len(node.peer_conn),
                )

                bundle = await assembler.assemble(wr)
                new_wr, new_wr_hash = processor.process_bundle(wr.core_index, bundle, wr.segment_root_lookup, True)

                assert new_wr_hash == vector.rep_hash
                assert new_wr == vector.work_rep

                logger.debug(
                    "Audit assertion successful",
                    peers=len(node.peer_conn),
                )
            except Exception as e:
                logger.error(
                    "Error occurred while testing node assertion",
                    err=str(e),
                    err_type=type(e).__name__,
                )

            # await asyncio.sleep(6)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_auditor():
    pytest.skip("Add latest vectors and test again!")
    await setup_processes(CLIENTS, [node_task], 30)
