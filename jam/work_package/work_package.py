from anyio import sleep
from numpy.ma.core import concatenate
from sympy.physics.units import ha

from jam.types import Bytes, Byte,
from jam.types.work.item import WorkItem, ExtrinsicSpec
from jam.types import Bytes, Vector, ByteArray32, Int
from jam.types.work.item import WorkItem
from jam.types.work.package import  WorkPackage
from jam.types.work.report import WorkResult, RefineLoad
from jam.utils.constants import MAX_EXPORT_ITEM, MAX_IMPORT_ITEM, EXTRINSIC_COUNT, MAX_WORK_PACKAGE_SIZE, SEGMENT_SIZE, REFINE_GAS, ACCUMULATION_GAS
from jam.utils.vrf.ietf import point_add
from jam.types.work.report import WorkResult, RefineLoad, WorkResults
from jam.utils.constants import MAX_EXPORT_ITEM, MAX_IMPORT_ITEM, EXTRINSIC_COUNT
from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError
from jam.types.work.report import WorkExecResult
from hashlib import blake2b
from jam.types.base.integers.fixed import U32
from math import floor
from jam.merklization.binary_merkle import BMRFunctions
from jam.types.work.report import WorkReport
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.base.dictionary import decodable_dictionary , Dictionary
from jam.types.protocol.crypto import OpaqueHash
from jam.hostCall.types import Segment, SegEle
from jam.types.work.report import ExecResults
from jam.types.protocol.crypto import Hash
from jam.merklization.binary_merkle import BMRFunctions
from math import ceil
from jam.hostCall.Refine import PsiR
from jam.hostCall.invocation import PsiI
from jam.types import CoreIndex
from jam.types.work.report import WorkReport, WorkPackageSpec
from jam.hostCall.Refine import PsiR
from jam.hostCall.invocation import PsiI
from jam.types import CoreIndex
from jam.erasure_coding.erasure_code import ErasureCode
from jam.utils.constants import BASIC_ERASURE_SIZE
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.types import Vector

@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class SegmentRootLookupDict(Dictionary[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

class WorkPackageProcessing(WorkResult):

    segment_root_lookup_dict: SegmentRootLookupDict = {}
    segments: Segment
    d: ExecResults
    specs: WorkPackageSpec

    def __init__(self):
        super().__init__()
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

    def _ext(self, w: WorkItem, d:ExecResults):
        result = []
        for item in d:
            first = blake2b(self.d)
            second = U32(len(d))
            if ExtrinsicSpec(hash=first, len=second) in w.extrinsic:
                result.append(item)
        return result

    def _imp_seg(self, w: WorkItem):
        result = []
        for s in self.segments:
            for (r, n) in w.import_segments:
                # merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == self.merkle.cd_merkle_fn(self.merkle,s):
                        result.append(s[n])
        return result

    def _justify_imp(self, w: WorkItem):
        result = []
        for s in self.segments:
            for (r, n) in w.import_segments:
                # merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == self.merkle.cd_merkle_fn(self.merkle, s):
                    result.append(self.merkle.merkle_path_fn(self.merkle, s, len(s), n))
        return result


    def wr_gen(self, p:WorkPackage, c: CoreIndex):
        """
        work result computation function
        Args:
            work package , core_index
        Return :
            Work Report
        """
        o, g = PsiI(p, int(c)).process()
        lookup_keys = []
        for item in p.items:
            for (h, n) in item.import_segments:
                if len(lookup_keys) <= 8:
                    lookup_keys.append(h)
        self.segment_root_lookup_dict = SegmentRootLookupDict({key: None for key in lookup_keys})
        def utils_i(j: int):
            w = p.items[int(j)]
            l = 0
            k = int(j)
            for i in range(k):
                l += p.items[i].extrinsic
            r, e, u = PsiR(int(c), p, o, WorkPackage._imp_seg(self, w), l)
            # h = blake2b(p)
            seg_ele = SegEle([Byte(0)] * 4104)
            segment_length = w.extrinsic
            zero_segment = Segment([seg_ele for _ in range(segment_length)])
            if len(e) == w.extrinsic:
                return r, u, e
            elif not isinstance(r, Bytes):
                return r, u, zero_segment
            else:
                return WorkExecResult(bad_exports=None), u,zero_segment

        r_list = []
        e_list = []
        for _j in range(len(p.items)):
            _r, _u, _e = utils_i(_j)
            comp = WorkPackage.item_to_result(p.items[_j], _r, _u)
            r_list.append(comp)
            e_list.append(_e)

        if not isinstance(o, Bytes):
            return None
        else:
            return WorkReport(package_spec=self.specs, context=p.context, core_index=c, authorizer_hash=p.code_hash, auth_output=o, segment_root_lookup=self.segment_root_lookup_dict, results=WorkResults(r_list), auth_gas_used=g)


    def segment_root_lookup(self, r: OpaqueHash) -> SegmentRoot:
        """
        segment root lookup function collapses a union of segment-roots and work-package hashes into segment-roots using the dictionary
        Args:
            r: hash

        Returns:
            r if r is already a segment root else Segment root from dictionary if r is a work package hash.
        """
        if r in self.segment_root_lookup_dict:
            return self.segment_root_lookup_dict[r]
        else:
            return r

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a45011a2302?v=0.6.4
    @staticmethod
    def item_to_result(item : WorkItem, result, gas):
        extrinsic_size = None
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + i.len

        refine_load = RefineLoad(gas_used=gas, imports=len(item.import_segments), exports=item.export_count,
                                 extrinsic_count=len(item.extrinsic), extrinsic_size=extrinsic_size)

        return WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=Hash.blake2b(item.payload),
                          accumulate_gas=item.accumulate_gas_limit, result=result, refine_load=refine_load)



    # https://graypaper.fluffylabs.dev/#/68eaa1f/1ad6001a2401?v=0.6.4
    @staticmethod
    def work_package_size(item :WorkItem, package: WorkPackage):
        auth_token = len(package.authorization)
        parameterization  = len(package.params)

        extrinsic_len = 0
        item_count = 0

        for x in package.items:
            for y in x.extrinsic:
                extrinsic_len = extrinsic_len  + y.len

            item_count = len(x.payload) + len(x.import_segments) * SEGMENT_SIZE + extrinsic_len

        package_size = auth_token + parameterization + item_count
        if package_size > MAX_WORK_PACKAGE_SIZE:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_WORK_PACKAGE_SIZE,
                "count of extrinsic more than are more than actual value"
            )

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1a2e011a4401?v=0.6.4
    @staticmethod
    def gas_limit( package: WorkPackage):
        total_refine_gas = 0
        total_accumulate_gas  = 0
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

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1cee001c1301?v=0.6.4
    @staticmethod
    def zero_padding(value: ByteArray32, n : Int):
        """
        Description: This function applies zero-padding to each element of a given list of byte arrays. The goal is to ensure that the length of every individual byte array becomes a multiple of a given integer nn. If an element's length is already a multiple of nn, no padding is added. Otherwise, the function appends the minimum number of 0 bytes required to reach the next multiple of nn. This is commonly used in Merkle tree constructions, erasure coding, cryptographic proofs, and blockchain data availability systems.

        Args :
            x (list) : List of byte arrays (strings or bytes) to be padded individually.
            n (int) : The target block size. Each element will be padded to a length that is a multiple of n

        Return :  New list containing padded byte arrays. Each element's length is now a multiple of n, padded with zeroes at the end.

        """
        hash_length = len(value)
        first_index = ((abs(hash_length) + n - 1) // n) + 1
        if hash_length // n != 0:
            padding_zero = n - first_index
            for i in range(padding_zero):
                value.append(0)
        return value

    # https://graypaper.fluffylabs.dev/#/68eaa1f/1b16001b6300?v=0.6.4
    @staticmethod
    def paged_proof(export_segment: Vector[ByteArray32]):
        """
        Description: The Paged-Proofs function PP takes a series of exported segments produced by work-items and prepares them for long-term storage and verification. It erasure-codes the segments, organizes them into pages of hashes, and generates subtree Merkle proofs. This allows anyone to verify the correctness of these segments using only the segments-root stored in the work-report.

        Args: s=[s1,s2,s3,...,sn] → List of exported segments generated by work-items of a work-package.

        Return:
            pages → Pages of hashes created from the erasure-coded exported segments.
            proofs → Subtree Merkle proofs for verifying correctness of segments using the segments-root.
            Output ensures data availability, long-term storage, and easy verification from the Imports DA system.

        """
        index = ceil(len(export_segment)/64)
        padding = []
        for x in range(index):
            # length need to be encoded
            path = BMRFunctions.merkle_path_fn(values=export_segment, size=6, index=x)
            leaf = BMRFunctions.leaf_page_fn(values=export_segment, size=6, index=x)
            merkle_path = bytes(len(path)) + path.encode()
            leaf =  bytes(len(leaf)) + leaf.encode()
            padding.append(WorkPackageProcessing.zero_padding(merkle_path + leaf, SEGMENT_SIZE))

        return padding

    def availability_specifier(self, package_hash: OpaqueHash, wp_bundle: ByteArray32, export_segment: Vector[ByteArray32]):
        """
        creates an availability specifier from the package hash, work-package bundle and the sequence of exported segments
        Args:
            package_hash:
            wp_bundle:
            export_segment:
        Returns:
            s: Availability specifier
        """
        l = len(wp_bundle)
        e = BMRFunctions.cd_merkle_fn(self.merkle, export_segment)
        n = len(export_segment)

        erasure_codec = ErasureCode()

        padded_wp_bundle = self.zero_padding(wp_bundle, BASIC_ERASURE_SIZE)
        encoded_wp_bundle = erasure_codec.encode(padded_wp_bundle)
        hashed_wp_bundle = []
        for item in encoded_wp_bundle:
            hashed_wp_bundle.append(item.blake2b(item.encode()))

        concatenated_export_segment = export_segment + self.paged_proof(export_segment)

        encoded_export_segment = []

        for item in concatenated_export_segment:
            encoded = erasure_codec.encode(item)
            encoded_export_segment.append(encoded)

        transposed_s = [[encoded_export_segment[j][i] for j in range(len(encoded_export_segment))] for i in range(len(encoded_export_segment[0]))]

        merkle_chunks_s = []
        for item in transposed_s:
            merkle_chunks_s.append(BMRFunctions.wb_merkle_fn(self.merkle, item))

        x = merkle_chunks_s + hashed_wp_bundle
        transposed_x = [[x[j][i] for j in range(len(x))] for i in range(len(x[0]))]

        x_caps: Vector[ByteArray32] = Vector([])

        for item in transposed_x:
            x_cap = ""
            for i in item:
                x_cap += i
            x_caps.append(x_cap)

        u = BMRFunctions.wb_merkle_fn(self.merkle, x_caps)

        return {
            package_hash,
            l,
            u,
            e,
            n
        }

