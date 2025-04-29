from math import ceil
from typing import Tuple

from jam.types.base.sequences.bytes import Bytes, Byte, ByteArray64
from jam.types.base.sequences.vector import Vector

from jam.types.base.integers.general import Int
from jam.types.base.integers.fixed import U8, U16, U64


from jam.types.work.item import WorkItem, ExtrinsicSpec
from jam.types.work.package import  WorkPackage
from jam.types.work.segment import Segments, Segment, MultiSegments
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

from tests.dummy.dummy_package import create_dummy_package
from tests.dummy.utils import create_dummy_bytes32

from jam.work_package.package_db import BundleStore, SegmentStore


class WorkPackageProcessing:

    segment_root_lookup_dict: SegmentRootLookup
    segments: MultiSegments
    # d: ??

    def __init__(self):
        self.merkle = BMRFunctions()

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def export_count (item : WorkItem):
        if item.export_count > MAX_EXPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXPORT_ITEM,
                "count of import segment are more than actual value"
            )

    #https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def import_count(item : WorkItem):
        if item.import_segments > MAX_IMPORT_ITEM:
            raise WorkPackageError (
                WorkPackagesErrorCode.BAD_IMPORT_ITEM,
                "count of import segment are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a9f001ad000?v=0.6.4
    @staticmethod
    def extrinsic_count(item : WorkItem):
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

    @staticmethod
    def fetch_extrinsics(w: WorkItem) -> Vector[Bytes]:
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
        data: Vector[Bytes] = Vector([])

        # <!-- Currently remains unclear -->
        # TODO: Fetch extrinsic from db / some pre-sent data whose hash and length are present in w.extrinsic

        return data

    @staticmethod
    def fetch_imports(w: WorkItem) -> MultiSegments:
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

        # We have to store EC Chunks (Shards) of Segments w Proofs into D3L, when segments are exported

        # Also we have to create and store mappings:
        # Mapping from wp hash -> segment root (this can be constructed via listening to reports) - done

        # Mapping from segment root -> erasure root & assurer - done
        # Mapping from erasure root + shard index -> bundle shard - done

        # On Guarantor Node
        # Mapping from segment root -> segments - done
        # Mapping from erasure root -> bundle  -done
        # index -> segment


        # How to store?
        # We merklize all the chunks and can we store entire tree?
        # Or should we just map  root -> hashes and store segments as hash -> segment

        # Cleanup Service?
        # A service to clear certain data if it expires or reach it's max storage duration

        #  For importing segments,
        # We first check if that segment_root is located in our DA system
        # if yes:
        #    then we fetch the segments directly from our DB / DA Layer / D3L
        # else:
        #    if we have all the segment chunks in DA:
        #         we reconstruct them to form segments
        #    else:
        #         we request unavailable shard from respective assurer
        #         and reconstruct them to form segments

        # Protocols to link up with DA Layer

        # TODO: Fetch proper segments
        segments: MultiSegments = MultiSegments([])

        # For other guarantors
        # Segment root -> erasure coded chunks & assurers

        # db.get(b"{segment_root}")

        # merkle_root = self.merkle.cd_merkle_fn(self.segments)
        #
        # for (r, n) in w.import_segments:
        #     if self.segment_root_lookup(r) == merkle_root:
        #             segments.append(self.segments[n])

        return segments

    def fetch_justifications(self, w: WorkItem) -> Vector[Vector[OpaqueHash]]:
        """
        Function J defined in Eqn 14.14
        Takes work item and compiles justifications of import segments data

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1bf0011bfe01?v=0.6.4
        Args:
            w: WorkItem
        Returns:
            Length prefixed justification
        """
        pages: Vector[Vector[OpaqueHash]] = Vector([])
        segments: Segments = Segments([])
        merkle_root = self.merkle.cd_merkle_fn(segments)

        # TODO: Compile proper justifications
        for (r, n) in w.import_segments:
            if self.segment_root_lookup(r) == merkle_root:
                pages.append(self.merkle.merkle_path_fn(segments, Int(0), n))
        return pages

    def generate_wr(self, p: WorkPackage, c: CoreIndex):
        """
        Work Report Computation function Ξ defined in Eqn 14.11

        Source:
            https://graypaper.fluffylabs.dev/#/68eaa1f/1b7c001be700?v=0.6.4
        Args:
            p: WorkPackage
            c: CoreIndex
        Returns:
            Work Report
        """
        o, g = PsiI(p, int(c)).process()
        lookup_keys = []
        for item in p.items:
            for (h, n) in item.import_segments:
                if len(lookup_keys) <= 8:
                    lookup_keys.append(h)


        # TODO: Build segment root lookup dictionary from DB
        self.segment_root_lookup_dict = SegmentRootLookup({})

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
            # r, e, u = PsiR(int(c), p, o, self.fetch_imports(w), l)

            # TODO: Fix later on receiving more clarity
            r, e, u = PsiR(int(c), p, o, self.segments, l)

            segment = Segment([Byte(0)] * 4104)
            segment_length = w.export_count
            zero_segment = Segments([segment for _ in range(segment_length)])

            if len(e) == w.export_count:
                return r, u, e
            elif not isinstance(r, Bytes):
                return r, u, zero_segment
            else:
                return WorkExecResult(bad_exports=None), u,zero_segment

        r_list = WorkResults([])
        e_list = MultiSegments([])

        for _j in range(len(p.items)):
            _r, _u, _e = utils_i(_j)

            comp = self.item_to_digest(p.items[_j], _r, _u)
            r_list.append(comp)
            e_list.append(_e)

        # TODO: Handle Errors and Segment Storage

        authorizer = p.code_hash + p.params
        p_a = Hash.blake2b(bytes(authorizer))

        h = Hash.blake2b(p.encode())
        e_bar_cap = Segments([])

        for segments in e_list:
            e_bar_cap.extend(segments)

        wp_bundle = WorkPackageBundle(package=p, extrinsics=Vector([]), import_segments=Vector([]), justifications=create_dummy_bytes32(), exports_count=U16(0))
        specs = self.availability_specifier(package_hash=h, wp_bundle=wp_bundle.encode(), export_segments=e_bar_cap)

        # inserting auditable bundle in db
        bundle_db = BundleStore()
        bundle_db.put(specs.erasure_root, wp_bundle)

        #inserting segments in db
        segment_db = SegmentStore()
        segment_db.put(export_segment=e_bar_cap, paged_proof=self.paged_proof(e_bar_cap))


        if not isinstance(o, Bytes):
            return None
        else:
            return WorkReport(package_spec=specs, context=p.context, core_index=c, authorizer_hash=p_a, auth_output=o, segment_root_lookup=self.segment_root_lookup_dict, results=r_list, auth_gas_used=g)


    def segment_root_lookup(self, r: OpaqueHash) -> SegmentRoot:
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
        if r in self.segment_root_lookup_dict:
            return self.segment_root_lookup_dict[r]
        else:
            return r

    # TODO: Change Work Result to Work Digest (0.6.4 Sync)
    @staticmethod
    def item_to_digest(item : WorkItem, result: WorkExecResult, gas: Gas) -> WorkResult:
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

        # l: WorkResult = WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=payload_hash,
        #                            accumulate_gas=item.accumulate_gas_limit, result=result, refinement_gas=gas,
        #                            import_count=U16(len(item.import_segments)), export_count=item.export_count,
        #                            extrinsic_count=U8(len(item.extrinsic)), extrinsic_size=extrinsic_size)
        #
        # return l

        imports_count: U16 = U16(len(item.import_segments))
        exports_count: U16 = U16(item.export_count)
        extrinsic_count: U8 = U8(len(item.extrinsic))

        refine_load = RefineLoad(gas_used=gas, imports=imports_count, exports=exports_count,
                                 extrinsic_count=extrinsic_count, extrinsic_size=extrinsic_size)

        return WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=payload_hash,
                          accumulate_gas=item.accumulate_gas_limit, result=result, refine_load=refine_load)

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
        hash_length = len(value)
        first_index = ((abs(hash_length) + n - 1) // n) + 1
        if hash_length % int(n) != 0:
            padding_zero = n - hash_length
            for i in range(padding_zero):
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
            path = self.merkle.merkle_path_fn(values=segments, size=Int(6), index=Int(x))
            print(f"path  ", path)
            leaf = self.merkle.leaf_page_fn(values=segments, size=Int(6), index=Int(x))
            merkle_path = bytes(len(path)) + Vector(path).encode()
            leaf =  bytes(len(leaf)) + leaf.encode()

            segment_proof = Segment(self.zero_padding(Bytes(merkle_path + leaf), SEGMENT_SIZE))
            pages.append(segment_proof)

        return pages

    def availability_specifier(self, package_hash: OpaqueHash, wp_bundle: Bytes, export_segments: Segments) -> WorkPackageSpec:
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
        l = len(wp_bundle)
        e = self.merkle.cd_merkle_fn(export_segments)
        n = len(export_segments)

        erasure_codec = ErasureCode()

        # Build Bundle Shards
        padded_wp_bundle = self.zero_padding(wp_bundle, BASIC_ERASURE_SIZE)
        encoded_wp_bundle = erasure_codec.encode(padded_wp_bundle)

        b_shards: Vector[OpaqueHash] = Vector([])
        for item in encoded_wp_bundle:
            b_shards.append(Hash.blake2b(item.encode()))

        # Build Segment Shards
        justified_segments: Segments = export_segments + self.paged_proof(export_segments)

        encoded_export_segments = Vector([])

        for item in justified_segments:
            encoded = erasure_codec.encode(item)
            encoded_export_segments.append(encoded)

        transposed_s = [Vector([encoded_export_segments[j][i] for j in range(len(encoded_export_segments))]) for i in range(len(encoded_export_segments[0]))]

        s_shards: Vector[OpaqueHash] = Vector([])
        for item in transposed_s:
            s_shards.append(self.merkle.wb_merkle_fn(item))

        # Build Complete Shard
        shards: Vector[Vector[OpaqueHash]] = Vector([b_shards, s_shards])
        transposed_shards = Vector([Vector([shards[j][i] for j in range(len(shards))]) for i in range(len(shards[0]))])

        clubbed_shards: Vector[ByteArray64] = Vector([])

        for item in transposed_shards:
            x_cap = b""
            for i in item:
                x_cap += bytes(i)
            clubbed_shards.append(ByteArray64(x_cap))

        u = self.merkle.wb_merkle_fn(clubbed_shards)

        # TODO: Store Package Hash, Segment Root, Erasure Root & Chunks Mapping
        # TODO: Distribute Shards on Request

        specification = WorkPackageSpec(hash=package_hash, length=l, erasure_root=u, exports_root=e, exports_count=n)
        return specification

    def process(self, package: WorkPackage, core: CoreIndex):
        print("Validating Work Package..")
        self.validate_wp(package)

        print("Building Work Report..")
        report = self.generate_wr(package, core)

        print(f"Generated Work Report {report}")

        print(f"Distributing Work Report to other  validators!")
        # TODO: Distribute WR to Guarantors CE135

        print()
