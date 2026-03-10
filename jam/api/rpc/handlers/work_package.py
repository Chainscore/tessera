"""
Work Package Handler

Handlers for work package and DA-related RPC methods.
"""

import asyncio

from jam.block import Block
from jam.incore import Processor, Bundler, Validator
from jam.state.state import State
from jam.storage.da import ReportsDA, SegmentsDA, PackageSegmentMap
from jam.storage.da.mappings import PackageStatusMap, PackageStatus
from jam.storage.da.packages import PackageDA
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.protocol.crypto import HeaderHash, OpaqueHash
from jam.types.protocol.core import CoreIndex, WorkPackageHash
from jam.types.work.package import WorkPackage, WorkPackageBundle
from jam.types.work.manifest import Extrinsics, Extrinsic
from jam.api.rpc.handlers.base import BaseHandler
from jam.api.rpc.types import RpcError
from jam.api.rpc.utils.serialization import parse_params
from jam.utils.assignment import assign_guarantors
from tsrkit_types import Bytes, String, Null, Uint, U32


class WorkPackageHandler(BaseHandler):
    """Handler for work package and DA-related RPC methods."""

    def work_report(self, params: list) -> bytes:
        """Returns the work-report with the given hash."""
        (wr_hash,) = parse_params([OpaqueHash], params)
        wr_da = ReportsDA(self.settings.d3l)

        try:
            wr = wr_da.get(wr_hash)
            return wr.encode()
        except KeyError:
            raise RpcError(2, "Work-report unavailable.")

    async def submit_work_package(self, params: list) -> None:
        """
        Submit a work-package to the guarantors assigned to the given core.

        If we are a guarantor for this core, process locally.
        Otherwise, forward via CE133 to the assigned guarantors.
        """
        from jam.network.protocols.ce_133 import WorkPackageCore, CE133Data

        core_index, encoded_wp, raw_extrinsics = parse_params(
            [CoreIndex, Bytes, list], params
        )

        wp = WorkPackage.decode(encoded_wp)
        extrinsics = Extrinsics([Extrinsic(Bytes(e)) for e in raw_extrinsics])

        val_map, index_map = assign_guarantors(self.jam)
        my_index = self.settings.validator_index(self.state)
        guarantors = index_map.get(core_index, [])

        if my_index in guarantors:
            # We are a guarantor for this core — process locally
            processor = Processor(self.jam)
            asyncio.create_task(processor.process(wp, core_index, extrinsics))
        else:
            # We are not assigned — store and forward to the actual guarantors via CE133
            wp_da = PackageDA(self.settings.d3l)
            wp_status_da = PackageStatusMap(self.settings.d3l)

            wp_da.put(wp)
            status = PackageStatus.empty()
            status.status = String("REPORTABLE")
            wp_status_da.put(wp.hash(), status)

            # Build CE133 data and transmit
            wc = WorkPackageCore(wp, core_index)
            data = CE133Data(
                package_len=Uint[32](len(wc.encode())),
                package_data=wc,
                extrinsics_len=Uint[32](len(extrinsics.encode())),
                extrinsics=extrinsics,
            )
            asyncio.create_task(self.router.dispatch(133, data))

        return None

    async def submit_work_package_bundle(self, params: list) -> None:
        """
        Submit a work-bundle to the guarantors assigned to the given core.

        Validates the WP, stores it, builds segment root lookup,
        then shares via CE134 with co-guarantors.
        If we are a guarantor — process bundle + collect guarantees + distribute report.
        Otherwise — forward to assigned guarantors.
        """
        from jam.network.protocols.ce_134 import CoreSegment, CE134Data

        core_index, encoded_bundle = parse_params([CoreIndex, Bytes], params)
        settings = self.settings

        bundle = WorkPackageBundle.decode(encoded_bundle)
        wp = bundle.package

        validator = Validator()
        if not validator.validate_wp(wp):
            raise RpcError(0, "Invalid work package")

        wp_da = PackageDA(settings.d3l)
        wp_status_da = PackageStatusMap(settings.d3l)
        wp_da.put(wp)

        ext_da = ItemExtrinsics(self.main_db)
        ext_da.store_processed(bundle.extrinsics)

        bundler = Bundler(self.jam)
        lookup = bundler.build_lookup(wp)

        status = PackageStatus.empty()
        status.status = String("REPORTABLE")
        wp_status_da.put(wp.hash(), status)

        cs = CoreSegment(core_index, lookup)
        data = CE134Data(
            map_len=U32(len(cs.encode())),
            core_segment=cs,
            bundle_len=U32(len(bundle.encode())),
            work_package_bundle=bundle,
        )

        val_map, index_map = assign_guarantors(self.jam)
        my_index = settings.validator_index(self.state)
        guarantors = index_map.get(core_index, [])

        if my_index in guarantors:
            # We are a guarantor — process locally via Processor.process()
            extrinsics = bundle.extrinsics
            processor = Processor(self.jam)
            asyncio.create_task(processor.process(wp, core_index, extrinsics))
        else:
            # Forward to the assigned guarantors via CE134
            asyncio.create_task(self.router.dispatch(134, data))

        return None

    def work_package_status(self, params: list) -> dict:
        """Returns the status of the given work-package."""
        header_hash, wp_hash, anchor_hash = parse_params(
            [HeaderHash, WorkPackageHash, HeaderHash], params
        )

        state = State.load(self.jam, header_hash)

        # Check anchor block
        try:
            anchor_block = Block.load(anchor_hash, self.main_db)
            if not anchor_block:
                return {"Failed": "Anchor block not found in database."}
        except Exception:
            return {"Failed": "Could not load anchor block."}

        # Get package and status
        wp_da = PackageDA(self.settings.d3l)
        wp_status_da = PackageStatusMap(self.settings.d3l)

        try:
            wp = wp_da.get(wp_hash)
            status = wp_status_da.get(wp_hash)

            if wp.context.anchor != anchor_hash:
                return {"Failed": "Anchor doesn't match."}
        except KeyError:
            return {"Failed": "No Record of wp found"}

        rep_da = ReportsDA(self.settings.d3l)

        from jam.utils.constants import LOOKUP_ANCHOR_MAX_AGE

        if status.status == String("FAILED"):
            return {"Failed": str(status.err)}

        elif (
            status.status != String("FAILED") and status.wr_hash.unwrap() == Null
        ) or status.status == String("REPORTABLE"):
            max_slot = int(wp.context.lookup_anchor_slot) + LOOKUP_ANCHOR_MAX_AGE
            remaining = max(0, max_slot - state.tau)
            return {"Reportable": {"remaining_blocks": remaining}}

        elif status.status == String("REPORTED"):
            wr_hash = status.wr_hash.unwrap()
            wr = rep_da.get(wr_hash)
            reported_in = status.reported_in.unwrap()
            reported_block = Block.load(reported_in, self.main_db)
            return {
                "Reported": {
                    "reported_in": {
                        "header_hash": reported_in,
                        "slot": int(reported_block.header.slot),
                    },
                    "core": int(wr.core_index),
                    "report_hash": wr_hash,
                }
            }

        elif status.status == String("READY"):
            wr_hash = status.wr_hash.unwrap()
            wr = rep_da.get(wr_hash)
            reported_in = status.reported_in.unwrap()
            reported_block = Block.load(reported_in, self.main_db)
            ready_in = status.ready_in.unwrap()
            ready_block = Block.load(ready_in, self.main_db)
            return {
                "Ready": {
                    "reported_in": {
                        "header_hash": reported_in,
                        "slot": int(reported_block.header.slot),
                    },
                    "core": int(wr.core_index),
                    "report_hash": wr_hash,
                    "ready_in": {
                        "slot": int(ready_block.header.slot),
                        "header_hash": ready_block.header.hash(),
                    },
                }
            }

        return {"Failed": "Work Package failed to process."}

    async def fetch_work_package_segments(self, params: list) -> list | None:
        """Fetches a list of segments from the DA layer, exported by the work-package."""
        wp_hash, indices = parse_params([WorkPackageHash, list], params)
        seg_da = SegmentsDA(self.settings.d3l)
        wpsr_da = PackageSegmentMap(self.settings.d3l)

        try:
            seg_root = wpsr_da.get(wp_hash)
        except KeyError:
            return None

        try:
            segs, proof_segs = seg_da.get(seg_root)
            req = []
            n = len(segs)

            for i in indices:
                if i >= n:
                    req.append(proof_segs[i - n].encode())
                else:
                    req.append(segs[i].encode())
            return req
        except KeyError:
            return None

    async def fetch_segments(self, params: list) -> list | None:
        """Fetches a list of segments from the DA layer, exported by a work-package."""
        seg_root, indices = parse_params([OpaqueHash, list], params)
        seg_da = SegmentsDA(self.settings.d3l)

        try:
            segs, proof_segs = seg_da.get(seg_root)
            req = []
            n = len(segs)

            for i in indices:
                if i >= n:
                    req.append(proof_segs[i - n].encode())
                else:
                    req.append(segs[i].encode())
            return req
        except KeyError:
            return None
