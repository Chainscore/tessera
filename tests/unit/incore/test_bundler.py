import asyncio
import json
from time import time

import pytest
import os

from jam.operations.handlers import WPBuilder as Builder

from jam.storage.da.mappings import (
    PackageSegmentMap,
    SegmentErasureMap,
    ReportHashAssurerMap,
    ErasureAssurerMap,
)
from jam.storage.da.reports import ReportsDA

from jam.models.protocol.core import CoreIndex, ValidatorIndex
from jam.models.work import Extrinsics, Extrinsic, Assurers
from jam.utils.benchmark import write_json

from jam.utils.constants import GENESIS_TS
from tests.integration.jamnp.utils.fetch_test_vectors import fetch_vectors

from tests.integration.utils.setup_processes import Client, Role, setup_processes
from tests.unit.incore.types import BundleVectors, BundleVector

CLIENTS = [Client(Role.VAL, 40001, theme="monokai")]

# NOTE: Use this for testing refinement / bundler
vectors: BundleVectors = BundleVectors([])
# fetch_vectors(1, 101, vectors)

async def node_task():
    from jam.log_setup import node_logger as logger
    from jam.incore.processor import Processor
    from jam.incore.bundler import Bundler

    ts = int((time() - GENESIS_TS) // 6)
    init_ts = ts

    # while True:
    while ts-init_ts != min(len(vectors), 100):
        from jam.network.start import node

        if node:
            bundler = Bundler()
            refiner = Processor()
            wp_iter = (ts - init_ts)

            # NOTE: Use this for testing refinement / bundler
            vector: BundleVector = vectors[wp_iter]
            wp = vector.work_package
            ext = vector.extrinsics
            core = vector.core_index

            # # NOTE: Use builder for generating random work packages
            # wp = Builder._build_package(wp_iter)
            # ext = Extrinsics([Extrinsic(b"") for i in range(len(wp.items))])
            # core = CoreIndex(1)

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

                # Assertions
                assert bundle == vector.bundle
                assert wr == vector.work_rep
                assert wr_hash == vector.rep_hash
                logger.info("ASSERTION SUCCESSFUL")

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

                # # For Test Vectors
                # vector = BundleVector(wp, core, ext, wr, wr_hash, bundle)
                # write_json("vectors/bundles", vector.to_json())

            except Exception as e:
                logger.error(
                    "Error occurred while bundling work package",
                    time_slot=ts,
                    iter=wp_iter,
                    total_iter=ts - init_ts,
                    err=str(e),
                    err_type=type(e).__name__,
                )

        ts += 1
        # await asyncio.sleep(6)


@pytest.mark.asyncio
@pytest.mark.skipif("ASYNC" not in os.environ, reason="async test")
async def test_bundler():
    pytest.skip("Add latest vectors and test again!")
    await setup_processes(CLIENTS, node_task, 5)
