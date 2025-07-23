import asyncio
from time import time

import pytest
import os

from jam.operations import Builder
from jam.types import CoreIndex, ValidatorIndex
from jam.types.work import Extrinsics, Extrinsic, Assurers
from jam.utils.constants import GENESIS_TS
from jam.work_package.processor import Processor
from jam.work_package.stores.mappings import (
    PackageSegmentMap,
    SegmentErasureMap,
    ReportHashAssurerMap,
    ErasureAssurerMap,
)
from jam.work_package.stores.reports import ReportsDA
from tests.integration.utils.setup_processes import Client, Role, setup_processes

CLIENTS = [Client(Role.VAL, 1, theme="monokai")]


async def node_task():
    from jam.logging import get_logger
    from jam.work_package.bundler import Bundler

    logger = get_logger()
    ts = int((time() - GENESIS_TS) // 6)
    init_ts = ts
    while True:
        from jam.network.node import node

        if node:
            bundler = Bundler(node)
            refiner = Processor(node)
            wp_iter = (ts - init_ts) % 4
            wp = Builder._build_package(wp_iter)
            ext = Extrinsics([Extrinsic(b"") for i in range(len(wp.items))])
            core = CoreIndex(1)

            logger.info(
                "Testing bundler",
                time_slot=ts,
                iter=wp_iter,
                total_iter=ts - init_ts,
                peers=len(node.peer_conn),
                connections=len(node.peer_conn),
            )

            try:
                lookup = bundler.build_lookup(wp)
                bundle = await bundler.build_bundle(wp, ext)

                logger.info(
                    "Bundle built",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    bundle=bundle.to_json(),
                )

                logger.debug("Compiling report..")
                wr, wr_hash = refiner.process_bundle(core, bundle, lookup)

                logger.info(
                    "Report compiled",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    wr_hash=wr_hash.hex(),
                    er_root=wr.package_spec.erasure_root.hex(),
                    sr_root=wr.package_spec.exports_root.hex(),
                    exp_count=wr.package_spec.exports_count,
                )

                from jam.settings import settings

                d3l = settings.d3l

                map_da = PackageSegmentMap(d3l)
                sr_er_da = SegmentErasureMap(d3l)
                rep_da = ReportsDA(d3l)
                wr_da = ReportHashAssurerMap(settings.d3l)
                er_da = ErasureAssurerMap(settings.d3l)

                # Store Report
                rep_da.put(wr_hash, wr)

                # Store Segment Root - Erasure Root Mapping
                sr_er_da.put(
                    root=wr.package_spec.exports_root, data=wr.package_spec.erasure_root
                )

                # Store Package Hash - Segment Root Mapping
                map_da.put(wr)

                assurers = Assurers([ValidatorIndex(1)])

                er_da.put(wr, assurers)
                wr_da.put(wr, assurers)

            except Exception as e:
                logger.error(
                    "Error occurred while bundling work package",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    err=str(e),
                    err_type=type(e).__name__,
                )
            finally:
                ts += 1

        await asyncio.sleep(6)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_bundler():
    await setup_processes(CLIENTS, node_task, 1000)
