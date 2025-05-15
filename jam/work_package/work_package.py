from math import ceil
from typing import Tuple
import os

from jam.config.settings import settings
from jam.db.kv import KVStore
from jam.types.base.sequences.bytes import Bytes, Byte, ByteArray12
from jam.types.base.sequences.vector import Vector

from jam.types.base.integers.general import Int
from jam.types.base.integers.fixed import U8, U16, U64


from jam.types.work.item import WorkItem
from jam.types.work.package import  WorkPackage
from jam.types.work.manifest import Segments, Segment, MultiSegments, Justifications, Justification, \
    Extrinsics, SegmentDict, MultiJustifications, MultiExtrinsics, ProvedSegments
from jam.types.work.shard import BundleShardHashes, BundleShardUnit, SegmentsShards, \
    SegmentsShard, SegmentsShardRoots, SegmentsShardUnit, ShardKey
from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError
from jam.types.work.report import (
    WorkResult,
    RefineLoad,
    WorkResults,
    WorkExecResult,
    WorkReport,
    WorkPackageSpec,
    SegmentRootLookup, WorkPackageBundle
)

from jam.utils.constants import (
    MAX_EXPORT_ITEM,
    MAX_IMPORT_ITEM,
    EXTRINSIC_COUNT,
    BASIC_ERASURE_SIZE,
    MAX_WORK_PACKAGE_SIZE,
    SEGMENT_SIZE,
    REFINE_GAS,
    ACCUMULATION_GAS
)

from jam.types.protocol.core import SegmentRoot, CoreIndex, Gas
from jam.types.protocol.crypto import OpaqueHash, Hash

from jam.erasure_coding.erasure_code import ErasureCode
from jam.merklization.binary_merkle import BMRFunctions


from jam.hostCall.Refine import PsiR
from jam.hostCall.invocation import PsiI
from jam.work_package.stores.audits import AuditShardsDA
from jam.work_package.stores.mappings import PackageSegmentMap, SegmentErasureMap, ErasureShardsMap
from jam.work_package.stores.reports import ReportsDA
from jam.work_package.stores.segments import SegmentsDA, SegmentShardsDA

from jam.types.protocol.crypto import WorkReportHash

from jam.network.protocols.ce_134 import WorkPackageSharing, CE134Data, CoreSegment
from jam.network.node import Node

class WorkPackageValidation:
    """Functions to validate work package"""

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def export_count(item: WorkItem):
        if item.export_count > MAX_EXPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXPORT_ITEM,
                "count of import segment are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def import_count(item: WorkItem):
        if item.import_segments > MAX_IMPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_IMPORT_ITEM,
                "count of import segment are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def extrinsic_count(item: WorkItem):
        if item.extrinsic > EXTRINSIC_COUNT:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXTRINSIC_COUNT,
                "count of extrinsic more than are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1ad6001a2401?v=0.6.4
    @staticmethod
    def work_package_size(package: WorkPackage):
        auth_token = len(package.authorization)
        parameterization = len(package.params)

        extrinsic_len = 0
        item_count = 0

        for x in package.items:
            for y in x.extrinsic:
                extrinsic_len = extrinsic_len + y.len

            item_count = len(x.payload) + len(x.import_segments) * SEGMENT_SIZE + extrinsic_len

        package_size = auth_token + parameterization + item_count
        if package_size > MAX_WORK_PACKAGE_SIZE:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_WORK_PACKAGE_SIZE,
                "count of extrinsic more than are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a2e011a4401?v=0.6.4
    @staticmethod
    def gas_limit(package: WorkPackage):
        total_refine_gas = 0
        total_accumulate_gas = 0
        for x in package.items:
            total_refine_gas = total_refine_gas + x.refine_gas_limit
            total_accumulate_gas = total_accumulate_gas + x.accumulate_gas_limit

        if total_refine_gas >= REFINE_GAS:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_REFINEMENT_GAS,
                "count of extrinsic more than are more than actual value"
            )
        if total_accumulate_gas >= ACCUMULATION_GAS:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_ACCUMULATION_GAS,
                "count of extrinsic more than are more than actual value"
            )

    def validate_wp(self, package: WorkPackage) -> bool:
        try:
            self.work_package_size(package)
            self.gas_limit(package)

            for item in package.items:
                self.export_count(item)
                self.import_count(item)
                self.extrinsic_count(item)

            print("Package Validated Successfully!")

            return True

        except WorkPackageError as err:
            print(f"WP Validation failed! Error {err.code}: {err.message}")
            return False

class WorkPackageProcessing:

    merkle: BMRFunctions
    sr_lookup: SegmentRootLookup
    segments_lookup: Vector[SegmentDict]

    def __init__(self):
        self.merkle = BMRFunctions()
        self.sr_lookup = SegmentRootLookup({})
        self.segments_lookup = Vector([])

    def build_lookup(self, p: WorkPackage) -> SegmentRootLookup:
        d3l = KVStore(settings.D3L_PATH)

        map_da = PackageSegmentMap(d3l)
        sr_lookup = SegmentRootLookup({})

        for item in p.items:
            for (h, n) in item.import_segments:
                s_root = map_da.get(h)
                if s_root and len(sr_lookup) < 8:
                    sr_lookup[h] = s_root

        self.sr_lookup = SegmentRootLookup
        d3l.close()
        return sr_lookup

    def lookup_root(self, r: OpaqueHash) -> SegmentRoot:
        """
        Segment root lookup function L defined in Eqn 14.12
        Collapses a union of segment-roots and work-package hashes into segment-roots using lookup dictionary

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c011b9c01?v=0.6.4
        Args:
            r: OpaqueHash
        Returns:
            r if r is already a segment root else Segment root from dictionary if r is a work package hash.
        """
        if r in self.sr_lookup:
            return self.sr_lookup[r]
        else:
            return r

    @staticmethod
    def fetch_extrinsics(w: WorkItem) -> Extrinsics:
        """
        Function X defined in Eqn 14.14
        Takes Work Item & retrieves its required extrinsic data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bcb011bd501?v=0.6.4
        Args:
           w: WorkItem
        Returns:
           Extrinsic data (Vector[Bytes])
        """
        data: Extrinsics = Extrinsics([])

        # TODO: Fetch extrinsic from db / some pre-sent data whose hash and length are present in w.extrinsic
        # Extrinsic Store Ready (Integration Remaining)

        return data

    def fetch_imports(self, w: WorkItem) -> Segments:
        """
        Function S defined in Eqn 14.14
        Takes Work Item & retrieves required import segments

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1be0011bea01?v=0.6.4
        Args:
            w: WorkItem
        Returns:
            Import Segments (Vector[Segment])
        """

        imports: Segments = Segments([])
        d3l = KVStore(settings.D3L_PATH)

        seg_da = SegmentsDA(d3l)
        sr_er_da = SegmentErasureMap(d3l)
        er_shards_da = ErasureShardsMap(d3l)
        shards_da = SegmentShardsDA(d3l)


        seg_dict = SegmentDict({})

        for (h, n) in w.import_segments:
            s_root = self.lookup_root(h)

            try:
                # Fetch segments directly from db first
                if s_root in seg_dict:
                    segments = seg_dict[s_root]
                    imports.append(segments[n])
                else:
                    segments, _ = seg_da.get(s_root)
                    seg_dict[s_root] = segments
                    imports.append(segments[n])

            except KeyError as e:
                print(f"Warning! {e}")
                print("Looking for segment shards in DA!")
                try:
                    e_root = sr_er_da.get(s_root)
                    shard_roots = er_shards_da.get_ss_roots(e_root)

                    if len(shard_roots) > 342:
                        # TODO: Reconstruct Shards
                        ...
                    else:
                        # TODO: Fetch Missing Shards
                        ...

                except KeyError as e2:
                    print(f"Warning! {e2}")
                    print("Fetching all segment shards from assurers!")

                    # TODO: Fetch All Shards

        self.segments_lookup.append(seg_dict)
        d3l.close()

        return imports

    def fetch_justifications(self, w: WorkItem, i: int) -> Justifications:
        """
        Function J defined in Eqn 14.14
        Takes work item and compiles justifications of import segments data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bf0011bfe01?v=0.6.4
        Args:
            w: Work Item
            i: Item Index
        Returns:
            Length prefixed justification
        """

        justifications: Justifications = Justifications([])
        seg_dict = self.segments_lookup[i]

        for (r, n) in w.import_segments:
            s_root = self.lookup_root(r)

            segments = seg_dict[s_root]
            pages = self.merkle.merkle_path_fn(segments, 0, int(n))
            justification = Justification(Int(len(pages)), pages)

            justifications.append(justification)

        return justifications

    # TODO: Change Work Result to Work Digest (0.6.4 Sync)
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

    def build_report(self, b: WorkPackageBundle, c: CoreIndex):
        """
        Work Report Computation function Ξ defined in Eqn 14.11
        To be used by main guarantor

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c001be700?v=0.6.4
        Args:
            b: WorkPackageBundle
            c: CoreIndex
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
            return WorkReport(package_spec=specs, context=p.context, core_index=c, authorizer_hash=p_a, auth_output=o, segment_root_lookup=self.sr_lookup, results=r_list, auth_gas_used=g)

    @staticmethod
    def zero_padding(value: Bytes, n : Int):
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
        print("paplu", settings.D3L_PATH)
        os.makedirs("db/30333/d3l", exist_ok=True)
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

    def build_bundle(self, p: WorkPackage) -> WorkPackageBundle:
        """Function to build Work Package Bundle"""

        all_imp = MultiSegments([])
        all_jfn = MultiJustifications([])
        all_ext = MultiExtrinsics([])

        for j, item in enumerate(p.items):
            # Fetch Imports
            imports = self.fetch_imports(item)
            all_imp.append(imports)

            # Fetch Justifications
            justifications = self.fetch_justifications(item, j)
            all_jfn.append(justifications)

            # Fetch Extrinsics
            extrinsics = self.fetch_extrinsics(item)
            all_ext.append(extrinsics)

        bundle = WorkPackageBundle(p, all_ext, all_imp, all_jfn)

        return bundle


    def process(self, package: WorkPackage, core: CoreIndex, extrinsics: Extrinsics):
        print("Validating Work Package..")
        validator = WorkPackageValidation()
        validator.validate_wp(package)

        d3l = KVStore(settings.D3L_PATH)

        # Build Segment Root Lookup Dictionary
        print("Building Lookup Dictionary..")
        lookup = self.build_lookup(package)

        # Build Work Package Bundle
        print("Building Work Package Bundle..")
        bundle = self.build_bundle(package)

        # TODO: Distribute Bundle to other Guarantors
        CE134 = WorkPackageSharing()

        core_segment = CoreSegment(core_index=core, segment_root_map=lookup, length=Int(1))

        data = CE134Data(work_package_bundle=bundle, core_segment=core_segment)

        node: Node = {

        }

        CE134.transmit(node=node, data=data)

        print("Building Work Report..")
        report = self.build_report(bundle, core)

        # Store Report
        reports_da = ReportsDA(d3l)

        wr_hash = Hash.blake2b(report.encode())
        reports_da.put(wr_hash, report)

        d3l.close()
        print(f"Generated Work Report {report}")

        print(f"Distributing Work Report to other  validators!")
        # TODO: Distribute WR to Guarantors CE135


    def bundle_process(self, core: CoreIndex, bundle: WorkPackageBundle, segment_lookup: SegmentRootLookup) -> Tuple[WorkReport, WorkReportHash]:
        d3l = KVStore(settings.D3L_PATH)

        self.sr_lookup = segment_lookup

        print("Building Work Report..")
        report = self.build_report(bundle, core)

        # Store Report
        reports_da = ReportsDA(d3l)

        wr_hash = Hash.blake2b(report.encode())
        reports_da.put(wr_hash, report)

        return report, wr_hash

