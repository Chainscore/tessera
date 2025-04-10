from anyio import sleep
from sympy.physics.units import ha

from jam.types import Bytes, Byte
from jam.types.work.item import WorkItem, ExtrinsicSpec
from jam.types.work.package import  WorkPackage
from jam.types.work.report import WorkResult, RefineLoad, WorkResults
from jam.utils.constants import MAX_EXPORT_ITEM, MAX_IMPORT_ITEM, EXTRINSIC_COUNT
from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError
from jam.types.work.report import WorkExecResult
from hashlib import blake2b
from jam.types.base.integers.fixed import U32
from math import floor
from jam.merklization.binary_merkle import BMRFunctions
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.base.dictionary import decodable_dictionary, Dict
from jam.types.protocol.crypto import OpaqueHash
from jam.hostCall.types import Segment, SegEle
from jam.types.work.report import ExecResults
from jam.types.protocol.crypto import Hash
from jam.hostCall.Refine import PsiR
from jam.hostCall.invocation import PsiI
from jam.types import CoreIndex
from jam.types.work.report import WorkReport, WorkPackageSpec


@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class SegmentRootLookupDict(Dict[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

class WorkPackage(WorkResult):
    segment_root_lookup_dict: SegmentRootLookupDict = {}
    segments: Segment
    d: ExecResults
    specs: WorkPackageSpec


    @staticmethod
    def export_count (item : WorkItem):
        if item.export_count > MAX_EXPORT_ITEM:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_EXPORT_ITEM,
                "count of import segment are more than actual value"
            )

    @staticmethod
    def import_count(item : WorkItem):
        if item.import_segments > MAX_IMPORT_ITEM:
            raise WorkPackageError (
                WorkPackagesErrorCode.BAD_IMPORT_ITEM,
                "count of import segment are more than actual value"
            )

    @staticmethod
    def extrinsic_count(item : WorkItem):
        if item.extrinsic > EXTRINSIC_COUNT:
            raise WorkPackageError(
                WorkPackagesErrorCode.BAD_IMPORT_ITEM,
                "count of extrinsic more than are more than actual value"
            )

    @staticmethod
    def zero_padding(arr : Bytes, n):
        hash_length = len(arr)
        first_index =  ((abs(hash_length) + n - 1) // n) + 1
        if hash_length // n != 0:
            padding_zero = n - first_index
            for i in range(padding_zero):
                arr.append(0)
        return arr


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
                merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == BMRFunctions.cd_merkle_fn(merkle,s):
                        result.append(s[n])
        return result

    def _justify_imp(self, w: WorkItem):
        result = []
        for s in self.segments:
            for (r, n) in w.import_segments:
                merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == BMRFunctions.cd_merkle_fn(merkle, s):
                    result.append(BMRFunctions.merkle_path_fn(merkle, s, len(s), n))
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

    @staticmethod
    def item_to_result(item : WorkItem, result, gas):
        extrinsic_size = None
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + i.len

        refine_load = RefineLoad(gas_used=gas, imports=len(item.import_segments), exports=item.export_count,
                                 extrinsic_count=len(item.extrinsic), extrinsic_size=extrinsic_size)

        return WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=Hash.blake2b(item.payload),
                          accumulate_gas=item.accumulate_gas_limit, result=result, refine_load=refine_load)