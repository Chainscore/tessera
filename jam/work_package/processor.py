import json
from math import ceil
from time import time
from typing import Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from jam.config.logging import logger
from jam.config.settings import settings

from jam.execution.host_calls.invocations.is_authorized import PsiI
from jam.execution.host_calls.invocations.refine import PsiR

from jam.types.base import Null

from jam.types.base.integers.general import Int
from jam.types.base.integers.fixed import U8, U16, U64, U32
from jam.types.base.sequences.bytes import Bytes, Byte, ByteArray12
from jam.types.base.sequences.vector import Vector

from jam.types.extrinsics import ValidatorSignature
from jam.types.extrinsics.guarantees import ValidatorSignatures

from jam.types.protocol.core import CoreIndex, Gas, TimeSlot, ExportsRoot
from jam.types.protocol.crypto import OpaqueHash, Hash, Ed25519Signature, WorkReportHash

from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage
from jam.types.work.manifest import (
    Segments,
    Segment,
    MultiSegments,
    Extrinsics,
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

from jam.utils.constants import BASIC_ERASURE_SIZE, SEGMENT_SIZE, MAX_WORK_REPORT_SIZE



from jam.erasure_coding.erasure_code import ErasureCode
from jam.merklization.binary_merkle import BMRFunctions


from jam.work_package.bundler import Bundler
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import ErasureShardsMap
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentsDA, SegmentShardsDA
from jam.work_package.validator import Validator

from jam.network.node import Node


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
        extrinsic_size: U64 = U64(0)
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

        # ------------------------------------------ IS AUTH INVOCATION ------------------------------------------
        logger.info(f"Checking authorization..")
        start_time = time()
        # Auth Output o & Gas g
        o, g = PsiI(p, c).execute()
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"Auth check done in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")
        # ------------------------------------------ -- ---- ---------- ------------------------------------------

        s_result = 0

        def utils_i(j: int) -> Tuple[WorkExecResult, Gas, Segments]:
            """
            Function I defined in Eqn 14.11
            Performs Ordered Accumulation of work items in a package p

            https://graypaper.fluffylabs.dev/#/cc517d7/1b3f011b8d01?v=0.6.5
            """

            nonlocal s_result
            w = p.items[j]

            l = 0
            k = int(j)
            for i in range(k):
                l += p.items[i].export_count

            # ------------------------------------------ REFINE INVOCATION ------------------------------------------
            logger.info(f"Refining Work Item {j}..")
            start_time = time()
            r, e, u = PsiR(j, p, o, b.import_segments, l).execute()
            end_time = time()
            total_time = end_time-start_time
            logger.info(f"Refined Work Item {j} in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")
            # ------------------------------------------ ----------------- ------------------------------------------

            segment = Segment([Byte(0)] * 4104)
            segment_length = w.export_count
            zero_segments = Segments([segment for _ in range(segment_length)])

            z = len(o) + s_result

            if r.get_key() != "ok":
                return r, u, zero_segments
            elif z + len(r.get_value()) > MAX_WORK_REPORT_SIZE:
                return WorkExecResult({"result_oversize": Null}), u, zero_segments
            elif len(e) != w.export_count:
                return WorkExecResult({"bad_exports": Null}), u, zero_segments
            else:
                s_result += len(r.get_value())
                return r, u, e


        # Work Results, r
        r_list = WorkResults([])

        # Exported Segments
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

        logger.info(f"Exported {len(e_bar_cap)} Segments!")

        # Availability Specification, s
        logger.info(f"Building availability specification..")
        start_time = time()
        specs = self.availability_specifier(package_hash=h, wp_bundle=b.encode(), export_segments=e_bar_cap)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"Specification built in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        logger.info(f"Compiling Report..")
        report = WorkReport(package_spec=specs, context=p.context, core_index=c, authorizer_hash=p.a, auth_output=Bytes(o), segment_root_lookup=sr_lookup, results=r_list, auth_gas_used=Gas(g))

        return report

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
        e = ExportsRoot(self.merkle.cd_merkle_fn(export_segments))
        logger.info(f"Exports Root calculated - {e}")

        # Segments Count, n
        n = len(export_segments)

        erasure_codec = ErasureCode()

        # Access DA
        d3l = settings.d3l
        audits = settings.audit

        # Build Bundle Shards
        audits_da = AuditShardsDA(audits)

        logger.info(f"Building bundle shards..")

        start_time = time()
        padded_wp_bundle = self.zero_padding(Bytes(wp_bundle), BASIC_ERASURE_SIZE)
        end_time = time()
        total_time = end_time-start_time
        logger.info(f"bundle padded in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        start_time = time()
        bundle_shards = erasure_codec.encode(padded_wp_bundle)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"bundle erasure coded in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        bs_hashes = BundleShardHashes([])

        logger.info(f"Storing bundle shards..")
        start_time = time()
        for si, bs in enumerate(bundle_shards):
            # start_time_a = time()
            bs_hash = Hash.blake2b(bs.encode())
            # end_time_a = time()
            # total_time = end_time_a - start_time_a
            # logger.info(f"hashed {si} in {total_time} seconds")

            bs_unit = BundleShardUnit(U16(si), bs)

            # Store Bundle Shard
            audits_da.put(bs_hash, bs_unit)
            bs_hashes.append(bs_hash)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"bundle chunks stored in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")


        # Store Exported Segments
        seg_da = SegmentsDA(d3l)

        logger.info(f"Storing segments..")
        start_time = time()
        proofs = self.paged_proof(export_segments)
        proved_segments = ProvedSegments(segment=export_segments, proof=proofs)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"proofs built in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        start_time = time()
        seg_da.put(e, proved_segments)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"proofs stored in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        # Build Segment Shards
        s_shards_da = SegmentShardsDA(d3l)

        logger.info(f"Building segment shards..")
        justified_segments: Segments = export_segments
        justified_segments.extend(proofs)

        all_chunks = Vector([])

        start_time = time()
        for item in justified_segments:
            seg_chunks = erasure_codec.encode(item)
            all_chunks.append(seg_chunks)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"segments erasure coded in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        start_time = time()
        segments_shards = SegmentsShards(
            [SegmentsShard(
                [ByteArray12(all_chunks[j][i]) for j in range(len(all_chunks))]
            ) for i in range(len(all_chunks[0]))])

        end_time = time()
        total_time = end_time - start_time
        logger.info(f"segments shards Transpose in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        ss_roots = SegmentsShardRoots([])

        logger.info(f"Storing segment shards..")
        start_time = time()
        for si, ss in enumerate(segments_shards):
            # start_time_a = time()
            ss_root = self.merkle.wb_merkle_fn(ss)
            # end_time_a = time()
            # total_time = end_time_a - start_time_a
            # logger.info(f"merklized {si} in {total_time} seconds")

            ss_unit = SegmentsShardUnit(U16(si), ss)

            # Store Segments Shard
            s_shards_da.put(ss_root, ss_unit)
            ss_roots.append(ss_root)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"segment chunks stored in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        # Build Complete Shard Key
        if len(ss_roots) != 1023 or len(bs_hashes) != 1023:
            raise ValueError("Length of both batches should be 1023")

        shards_keys = Vector([])
        for i in range(1023):
            shards_key = ShardKey(bs_hashes[i], ss_roots[i])
            shards_keys.append(shards_key.encode())

        # Erasure Root
        start_time = time()
        u = self.merkle.wb_merkle_fn(shards_keys)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"Erasure Root calculated - {u} in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        # Store Erasure Root - Shards Mapping
        er_shards_da = ErasureShardsMap(d3l)

        logger.info("Storing shards mappings..")
        start_time = time()
        er_shards_da.put_batch(u, ss_roots, bs_hashes)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"stored mappings in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        logger.info(f"Compiling availability specification..")
        start_time = time()
        spec = WorkPackageSpec(hash=package_hash, length=U32(l), erasure_root=u, exports_root=e, exports_count=U16(n))
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"compiled spec in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        return spec

    def process_bundle(self, core: CoreIndex, bundle: WorkPackageBundle, sr_lookup: SegmentRootLookup) -> Tuple[WorkReport, WorkReportHash]:
        # Generate Report
        logger.info("Building Work Report..")
        start_time = time()
        report = self.build_report(bundle, core, sr_lookup)
        end_time = time()
        total_time = end_time - start_time
        logger.info(f"Report compiled in {total_time} seconds. (~ 1/{6 // total_time}th of a slot)")

        wr_hash = Hash.blake2b(report.encode())
        logger.info(f"Generated Work Report with hash {wr_hash}")

        # Access DA
        d3l = settings.d3l

        # Store Report
        reports_da = ReportsDA(d3l)
        reports_da.put(wr_hash, report)
        logger.info(f"Stored Work Report with hash {wr_hash}")

        return report, wr_hash

    def process(self, package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
        from jam.network.protocols.ce_134 import WorkPackageSharing, CE134Data, CoreSegment
        from jam.network.protocols.ce_135 import WorkReportDistribution, CE135Data

        logger.info("Validating Work Package..")
        validator = Validator()
        validator.validate_wp(package)

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

        responses = CE134.transmit(node=self.node, data=data)

        # Build & Store Report
        wr, wr_hash = self.process_bundle(core, bundle, lookup)

        # Self guarantee
        port = 30333
        my_keys = json.load(open("seeds/keys.json"))[str(port)]
        ed25519_key = Ed25519PrivateKey.from_private_bytes(
            bytes.fromhex(my_keys["ed25519_private"][2:])
        )

        # Build Guarantee
        logger.info(f"Building guarantees..")
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
        logger.info(f"Distributing Work Report to other validators..")
        if len(guarantees) > 1:
            CE135 = WorkReportDistribution()
            data = CE135Data(report=wr, slot=TimeSlot(0), len=Int(len(guarantees)), signatures=guarantees)

            responses = CE135.transmit(node=self.node, data=data)

        return wr, wr_hash