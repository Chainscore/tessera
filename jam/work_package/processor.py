import os
import json
from math import ceil
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.config.logging import logger
from jam.config.settings import settings
from jam.db.kv import KVStore
from jam.types import Ed25519Signature, TimeSlot
from jam.types.base.sequences.bytes import Bytes, Byte, ByteArray12
from jam.types.base.sequences.vector import Vector

from jam.types.base.integers.general import Int
from jam.types.base.integers.fixed import U8, U16, U64
from jam.types.extrinsics import ValidatorSignature
from jam.types.extrinsics.guarantees import ValidatorSignatures

from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage
from jam.types.work.manifest import (
    Segments,
    Segment,
    MultiSegments,
    Extrinsics,
    SegmentDict,
    ProvedSegments
)
from jam.types.work.shard import (
    BundleShardHashes,
    BundleShardUnit,
    SegmentsShards,
    SegmentsShard,
    SegmentsShardRoots,
    SegmentsShardUnit,
    ShardKey
)
from jam.types.work.report import (
    WorkResult,
    RefineLoad,
    WorkResults,
    WorkExecResult,
    WorkReport,
    WorkPackageSpec,
    SegmentRootLookup,
    WorkPackageBundle
)

from jam.utils.constants import BASIC_ERASURE_SIZE, SEGMENT_SIZE

from jam.types.protocol.core import CoreIndex, Gas
from jam.types.protocol.crypto import OpaqueHash, Hash

from jam.erasure_coding.erasure_code import ErasureCode
from jam.merklization.binary_merkle import BMRFunctions


from jam.hostCall.Refine import PsiR
from jam.hostCall.invocation import PsiI
from jam.work_package.bundler import Bundler
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentsDA, SegmentShardsDA

from jam.types.protocol.crypto import WorkReportHash

from jam.network.node import Node
from jam.work_package.validator import Validator


class Processor:

    node: Node
    merkle: BMRFunctions

    def __init__(self, node: Node):
        self.merkle = BMRFunctions()
        self.node = node


    @staticmethod
    def zero_padding(value: Bytes, n: Int):
        """
        Zero Padding function P defined in Eqn 14.17
        Ensures that the length of individual byte array becomes a multiple of a given integer n.

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1c08011c2d01?v=0.6.5
        Args:
            value (Bytes) : Octet Array to be padded.
            n (Int) : The target block size. Each element will be padded to a length that is a multiple of n
        Returns:
            New list containing padded byte arrays. Each element's length is now a multiple of n, padded with zeroes at the end.
        """

        length = len(value)
        padding = n - (((length + n - 1) % n) + 1)

        for i in range(padding):
            value.append(Byte(0))

        return value

    def paged_proof(self, segments: Segments) -> Segments:
        """
        Page Proof function P defined in Eqn 14.10
        Compiles Justifications for exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1b2a001b8b00?v=0.6.5
        Args:
            segments (Segments): List of exported segments
        Returns:
            Proofs of size same as segments
        """
        page_count = ceil(len(segments)/64)

        pages: Segments = Segments([])
        for x in range(page_count):
            path = self.merkle.merkle_path_fn(values=segments, size=6, index=x)
            leaf = self.merkle.leaf_page_fn(values=segments, size=6, index=x)
            merkle_path = bytes(len(path)) + Vector(path).encode()
            leaf =  bytes(len(leaf)) + leaf.encode()

            segment_proof = Segment(self.zero_padding(Bytes(merkle_path + leaf), SEGMENT_SIZE))
            pages.append(segment_proof)

        return pages



    @staticmethod
    def item_to_digest(item: WorkItem, result: WorkExecResult, gas: Gas) -> WorkResult:
        """
        Item to Digest function C defined in Eqn 14.8

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1a6a011a5002?v=0.6.5
        Args:
            item: WorkItem
            result: WorkExecResult
            gas: Gas
        Returns:
            Work Digest
        """
        extrinsic_size: U64 = 0
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + i.len

        payload_hash = Hash.blake2b(bytes(item.payload))

        imports_count: U16 = U16(len(item.import_segments))
        exports_count: U16 = U16(item.export_count)
        extrinsic_count: U8 = U8(len(item.extrinsic))

        refine_load = RefineLoad(gas_used=gas, imports=imports_count, exports=exports_count,
                                 extrinsic_count=extrinsic_count, extrinsic_size=extrinsic_size)

        return WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=payload_hash,
                          accumulate_gas=item.accumulate_gas_limit, result=result, refine_load=refine_load)

    def build_report(self, b: WorkPackageBundle, c: CoreIndex, sr_lookup: SegmentRootLookup):
        """
        Work Report Computation function Ξ defined in Eqn 14.11
        To be used by main guarantor

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c001be700?v=0.6.4
        Args:
            b: Work Package Bundle
            c: Core Index
            sr_lookup: Segment Root Lookup
        Returns:
            Work Report
        """

        # Work Package, p
        p = b.package

        # Auth Output o & Gas g
        o, g = PsiI(p, int(c)).process()

        def utils_i(j: int) -> Tuple[WorkExecResult, Gas, Segments]:
            """
            Function I defined in Eqn 14.11
            Performs Ordered Accumulation of work items in a package p

            https://graypaper.fluffylabs.dev/#/cc517d7/1b3f011b8d01?v=0.6.5
            """

            w = p.items[j]

            l = 0
            k = int(j)
            for i in range(k):
                l += p.items[i].export_count

            r, e, u = PsiR(int(c), p, o, b.import_segments, l)

            segment = Segment([Byte(0)] * 4104)
            segment_length = w.export_count
            zero_segment = Segments([segment for _ in range(segment_length)])

            if len(e) == w.export_count:
                return r, u, e
            elif not isinstance(r, Bytes):
                return r, u, zero_segment
            else:
                return WorkExecResult(bad_exports=None), u,zero_segment

        # Work Results, r
        r_list = WorkResults([])

        e_list = MultiSegments([])

        for _j in range(len(p.items)):
            _r, _u, _e = utils_i(_j)

            comp = self.item_to_digest(p.items[_j], _r, _u)
            r_list.append(comp)
            e_list.append(_e)


        # Work Package Hash, h
        h = Hash.blake2b(p.encode())

        # Accumulate all exported segments
        e_bar_cap = Segments([])
        for segments in e_list:
            e_bar_cap.extend(segments)

        # Availability Specification, s
        specs = self.availability_specifier(package_hash=h, wp_bundle=b.encode(), export_segments=e_bar_cap)

        # Authorizer Hash, a
        authorizer = p.code_hash + p.params
        p_a = Hash.blake2b(bytes(authorizer))

        if not isinstance(o, Bytes):
            return None
        else:
            return WorkReport(package_spec=specs, context=p.context, core_index=c, authorizer_hash=p_a, auth_output=o, segment_root_lookup=sr_lookup, results=r_list, auth_gas_used=g)

    def availability_specifier(self, package_hash: OpaqueHash, wp_bundle: bytes, export_segments: Segments) -> WorkPackageSpec:
        """
        Availability Specification function defined in Eqn 14.16
        Creates a package specification from the package hash, work-package bundle and the sequence of exported segments

        Source:
            https://graypaper.fluffylabs.dev/#/cc517d7/1c3a001cf000?v=0.6.5
        Args:
            package_hash (OpaqueHash): Hash of package
            wp_bundle (Bytes): Encoded Audit Bundle
            export_segments (Segments): Exported Segments
        Returns:
            s: Availability specifier
        """

        # Work Bundle Length, l
        l = len(wp_bundle)

        # Segment Root, e
        e = self.merkle.cd_merkle_fn(export_segments)

        # Segments Count, n
        n = len(export_segments)

        erasure_codec = ErasureCode()
        os.makedirs(settings.D3L_PATH, exist_ok=True)
        d3l = KVStore(settings.D3L_PATH)

        # Build Bundle Shards
        audits_da = AuditShardsDA(d3l)

        padded_wp_bundle = self.zero_padding(Bytes(wp_bundle), BASIC_ERASURE_SIZE)
        bundle_shards = erasure_codec.encode(padded_wp_bundle)

        bs_hashes = BundleShardHashes([])

        for si, bs in enumerate(bundle_shards):
            bs_hash = Hash.blake2b(bs.encode())

            bs_unit = BundleShardUnit(U16(si), bs)

            # Store Bundle Shard
            audits_da.put(bs_hash, bs_unit)
            bs_hashes.append(bs_hash)


        # Store Exported Segments
        seg_da = SegmentsDA(d3l)

        proofs = self.paged_proof(export_segments)
        proved_segments = ProvedSegments(segment=export_segments, proof=proofs)
        seg_da.put(e, proved_segments)

        # Build Segment Shards
        s_shards_da = SegmentShardsDA(d3l)

        justified_segments: Segments = export_segments
        justified_segments.extend(proofs)

        all_chunks = Vector([])

        for item in justified_segments:
            seg_chunks = erasure_codec.encode(item)
            all_chunks.append(seg_chunks)
        segments_shards = SegmentsShards(
            [SegmentsShard(
                [ByteArray12(all_chunks[j][i]) for j in range(len(all_chunks))]
            ) for i in range(len(all_chunks[0]))])

        ss_roots = SegmentsShardRoots([])
        for si, ss in enumerate(segments_shards):
            ss_root = self.merkle.wb_merkle_fn(ss)

            ss_unit = SegmentsShardUnit(U16(si), ss)

            # Store Segments Shard
            s_shards_da.put(ss_root, ss_unit)
            ss_roots.append(ss_root)


        # Build Complete Shard Key
        if len(ss_roots) != 1023 or len(bs_hashes) != 1023:
            raise ValueError("Length of both batches should be 1023")

        shards_keys = Vector([])
        for i in range(1023):
            shards_key = ShardKey(bs_hashes[i], ss_roots[i])
            shards_keys.append(shards_key.encode())

        # Erasure Root
        u = self.merkle.wb_merkle_fn(shards_keys)

        # Store Erasure Root - Shards Mapping
        er_shards_da = ErasureShardsMap(d3l)

        er_shards_da.put_batch(u, ss_roots, bs_hashes)

        spec = WorkPackageSpec(hash=package_hash, length=l, erasure_root=u, exports_root=e, exports_count=n)

        d3l.close()
        return spec

    def process_bundle(self, core: CoreIndex, bundle: WorkPackageBundle, sr_lookup: SegmentRootLookup) -> Tuple[WorkReport, WorkReportHash]:
        d3l = KVStore(settings.D3L_PATH)
        reports_da = ReportsDA(d3l)

        # Generate Report
        logger.info("Building Work Report..")

        report = self.build_report(bundle, core, sr_lookup)
        wr_hash = Hash.blake2b(report.encode())

        logger.info(f"Generated Work Report with hash {wr_hash}")

        # Store Report
        reports_da.put(wr_hash, report)
        d3l.close()

        return report, wr_hash

    async def process(self, package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
        from jam.network.protocols.ce_134 import WorkPackageSharing, CE134Data, CoreSegment
        from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data

        logger.info("Validating Work Package..")
        validator = Validator()
        validator.validate_wp(package)

        d3l = KVStore(settings.D3L_PATH)

        bundler = Bundler()

        # Build Segment Root Lookup Dictionary
        logger.info("Building Lookup Dictionary..")
        lookup = bundler.build_lookup(package)

        # Build Work Package Bundle
        logger.info("Building Work Package Bundle..")
        bundle = bundler.build_bundle(package)

        # Distribute Bundle to other Guarantors CE134
        CE134 = WorkPackageSharing()

        core_segment = CoreSegment(core_index=core, segment_root_map=lookup, length=Int(len(lookup)))
        data = CE134Data(work_package_bundle=bundle, core_segment=core_segment)

        responses = await CE134.transmit(node=self.node, data=data)

        # Build & Store Report
        wr, wr_hash = self.process_bundle(core, bundle, lookup)

        # Self guarantee
        port = 30333
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(my_keys["ed25519_private"][2:])
        )

        # Build Guarantee
        payload = wr.core_index.encode() + wr.encode()
        guarantee = b"jam_guarantee" + Hash.blake2b(payload).encode()

        # Sign the Guarantee
        sign = Ed25519Signature(ed25519_key.sign(guarantee))

        og_guarantee = ValidatorSignature(validator_index=U16(0), signature=sign)

        # Check majority & Build guarantees:
        guarantees = ValidatorSignatures([og_guarantee])
        for response in responses:
            if response.work_report_hash == wr_hash:
                guarantee = ValidatorSignature(validator_index=U16(0), signature=response.ed25519_signature)
                guarantees.append(guarantee)


        # Distribute Guaranteed WR to Validators CE135
        logger.info(f"Distributing Work Report to other  validators!")
        if len(guarantees) > 1:
            CE135 = WorkReportDistribution()
            data = CE135Data(report=wr, slot=TimeSlot(0), len=Int(len(guarantees)), signatures=guarantees)

            responses = await CE135.transmit(node=self.node, data=data)

        return wr, wr_hash