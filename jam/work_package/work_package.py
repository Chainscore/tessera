from sympy.physics.units import ha

from jam.types import Bytes
from jam.types.work.item import WorkItem, ExtrinsicSpec
from jam.types.work.package import  WorkPackage
from jam.utils.constants import MAX_EXPORT_ITEM, MAX_IMPORT_ITEM, EXTRINSIC_COUNT
from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError
from jam.types.work.report import WorkExecResult
from hashlib import blake2b
from jam.types.base.integers.fixed import U32
from math import floor
from jam.merklization.binary_merkle import BMRFunctions
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.protocol.crypto import OpaqueHash

@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class SegmentRootLookupDict(Dictionary[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

class WorkPackage:

    segment_root_lookup_dict: SegmentRootLookupDict = {}

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

    @staticmethod
    def _ext(w: WorkItem, d):
        result = []
        for item in d:
            first = blake2b(d)
            second = U32(len(d))
            if ExtrinsicSpec(hash=first, len=second) in w.extrinsic:
                result.append(item)
        return result

    def _imp_seg(self, w: WorkItem, segments):
        result = []
        for s in segments:
            for (r, n) in w.import_segments:
                merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == BMRFunctions.cd_merkle_fn(merkle,s):
                        result.append(s[n])
        return result

    def _verify_imp(self, w: WorkItem, segments):
        result = []
        for s in segments:
            for (r, n) in w.import_segments:
                merkle = BMRFunctions()
                if WorkPackage.segment_root_lookup(self, r) == BMRFunctions.cd_merkle_fn(merkle, s):
                    result.append(BMRFunctions.merkle_path_fn(merkle, s, len(s), n))
        return result


    @staticmethod
    def wr_i(p:WorkPackage, j:int):
        print("utils for wok result computation")


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
