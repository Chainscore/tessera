from jam.types import Bytes, Vector, ByteArray32, Int
from jam.types.work.item import WorkItem
from jam.types.work.package import  WorkPackage
from jam.types.work.report import WorkResult, RefineLoad
from jam.utils.constants import MAX_EXPORT_ITEM, MAX_IMPORT_ITEM, EXTRINSIC_COUNT, MAX_WORK_PACKAGE_SIZE, SEGMENT_SIZE, REFINE_GAS, ACCUMULATION_GAS
from jam.utils.vrf.ietf import point_add
from jam.work_package.error import WorkPackagesErrorCode, WorkPackageError
from math import floor
from jam.types.work.report import WorkReport
from jam.types.protocol.core import SegmentRoot, WorkPackageHash
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.crypto import Hash
from jam.merklization.binary_merkle import BMRFunctions
from math import ceil


@decodable_dictionary(key_type=WorkPackageHash, value_type=SegmentRoot)
class SegmentRootLookupDict(Dictionary[WorkPackageHash, SegmentRoot]):
    """contains all unique work-package hashes and segment root"""
    ...

class WorkPackageProcessing(WorkResult):

    segment_root_lookup_dict: SegmentRootLookupDict = {}

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
    def item_to_result(self, item : WorkItem, result, gas):

        extrinsic_size = None
        for i in item.extrinsic:
            extrinsic_size = extrinsic_size + i.len

        refine_load = RefineLoad( gas_used=gas, imports=len(item.import_segments) , exports=item.export_count, extrinsic_count=len(item.extrinsic), extrinsic_size=extrinsic_size)
        return WorkResult(service_id=item.service, code_hash=item.code_hash, payload_hash=Hash.blake2b(item.payload), accumulate_gas=item.accumulate_gas_limit , result=result, refine_load=refine_load)



    # https://graypaper.fluffylabs.dev/#/68eaa1f/1ad6001a2401?v=0.6.4
    @staticmethod
    def work_package_size(item :WorkItem, package: WorkPackage):
        auth_token = len(package.parameterization)
        parameterization  = len(package.parameterization)

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