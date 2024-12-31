"""Work report types for the JAM protocol."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Any, Tuple, Sequence, Optional, Union

from jam.types.base.integers import U16, U32
from jam.types.base.bytes import Bytes
from jam.types.base.vector import Vector
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ErasureRoot, ExportsRoot, WorkPackageHash
from jam.utils.codec.base import Codable

from jam.types.protocol.core import (
    ServiceId, Gas, CoreIndex
)
from jam.types.work.refine_context import RefineContext
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.constants import MAX_WORK_ITEMS

class WorkExecResult(Enum):
    """Work execution result enumeration."""
    OK = 0
    OUT_OF_GAS = 1
    PANIC = 2
    BAD_CODE = 3
    CODE_OVERSIZE = 4

@dataclass
class WorkResult(Codable):
    """Work result structure."""
    service_id: ServiceId
    code_hash: OpaqueHash
    payload_hash: OpaqueHash
    accumulate_gas: Gas
    result: Union[Bytes, WorkExecResult]

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [
            self.service_id,
            self.code_hash,
            self.payload_hash,
            self.accumulate_gas
        ]
        if isinstance(self.result, Bytes):
            sequence.append(self.result)
        return sequence

    def encode_size(self) -> int:
        size = sum(item.encode_size() for item in self.enc_sequence())
        if not isinstance(self.result, Bytes):
            size += 1  # For enum variant
        return size

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        if isinstance(self.result, Bytes):
            buffer[current_offset] = WorkExecResult.OK.value
            current_offset += 1
            for item in self.enc_sequence():
                size = item.encode_into(buffer, current_offset)
                current_offset += size
        else:
            buffer[current_offset] = self.result.value
            current_offset += 1
            for item in self.enc_sequence()[:-1]:  # Skip result
                size = item.encode_into(buffer, current_offset)
                current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        result_type = WorkExecResult(buffer[current_offset])
        current_offset += 1

        service_id, size = ServiceId.decode_from(buffer, current_offset)
        current_offset += size
        code_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        payload_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        accumulate_gas, size = Gas.decode_from(buffer, current_offset)
        current_offset += size

        if result_type == WorkExecResult.OK:
            result = Bytes(buffer[current_offset:])
            current_offset = len(buffer)
        else:
            result = result_type

        return WorkResult(
            service_id,
            code_hash,
            payload_hash,
            accumulate_gas,
            result
        ), current_offset - offset

@dataclass
class WorkPackageSpec(Codable):
    """Work package specification structure."""
    hash: WorkPackageHash
    length: U32
    erasure_root: ErasureRoot
    exports_root: ExportsRoot
    exports_count: U16

    def enc_sequence(self) -> Sequence[Codable]:
        return [
            self.hash,
            self.length,
            self.erasure_root,
            self.exports_root,
            self.exports_count
        ]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        hash_val, size = WorkPackageHash.decode_from(buffer, current_offset)
        current_offset += size
        length, size = U32.decode_from(buffer, current_offset)
        current_offset += size
        erasure_root, size = ErasureRoot.decode_from(buffer, current_offset)
        current_offset += size
        exports_root, size = ExportsRoot.decode_from(buffer, current_offset)
        current_offset += size
        exports_count, size = U16.decode_from(buffer, current_offset)
        current_offset += size
        return WorkPackageSpec(
            hash_val,
            length,
            erasure_root,
            exports_root,
            exports_count
        ), current_offset - offset

@dataclass
class SegmentRootLookupItem(Codable):
    """Segment root lookup item structure."""
    work_package_hash: WorkPackageHash
    segment_tree_root: OpaqueHash

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.work_package_hash, self.segment_tree_root]

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        work_package_hash, size = WorkPackageHash.decode_from(buffer, current_offset)
        current_offset += size
        segment_tree_root, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        return SegmentRootLookupItem(
            work_package_hash,
            segment_tree_root
        ), current_offset - offset

class SegmentRootLookup(Vector[SegmentRootLookupItem]):
    """Sequence of segment root lookup items."""
    def __init__(self, items: List[SegmentRootLookupItem]):
        super().__init__(items)
    
    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        items, size = VectorCodec.decode_from(SegmentRootLookupItem, buffer, offset)
        return SegmentRootLookup(items), size

@dataclass
class WorkReport(Codable):
    """Work report structure."""
    package_spec: WorkPackageSpec
    context: RefineContext
    core_index: CoreIndex
    authorizer_hash: OpaqueHash
    auth_output: Bytes
    segment_root_lookup: SegmentRootLookup
    results: List[WorkResult]  # Size 1..4

    def __init__(self, package_spec: WorkPackageSpec,
                 context: RefineContext,
                 core_index: CoreIndex,
                 authorizer_hash: OpaqueHash,
                 auth_output: Bytes,
                 segment_root_lookup: SegmentRootLookup,
                 results: List[WorkResult]):
        if not (1 <= len(results) <= MAX_WORK_ITEMS):
            raise ValueError(f"Number of results must be between 1 and {MAX_WORK_ITEMS}")
        self.package_spec = package_spec
        self.context = context
        self.core_index = core_index
        self.authorizer_hash = authorizer_hash
        self.auth_output = auth_output
        self.segment_root_lookup = segment_root_lookup
        self.results = results

    def enc_sequence(self) -> Sequence[Codable]:
        sequence: List[Codable] = [
            self.package_spec,
            self.context,
            self.core_index,
            self.authorizer_hash,
            self.auth_output,
            self.segment_root_lookup
        ]
        sequence.extend(self.results)
        return sequence

    def encode_size(self) -> int:
        return sum(item.encode_size() for item in self.enc_sequence())

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        for item in self.enc_sequence():
            size = item.encode_into(buffer, current_offset)
            current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: bytes, offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        package_spec, size = WorkPackageSpec.decode_from(buffer, current_offset)
        current_offset += size
        context, size = RefineContext.decode_from(buffer, current_offset)
        current_offset += size
        core_index, size = CoreIndex.decode_from(buffer, current_offset)
        current_offset += size
        authorizer_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        auth_output = Bytes(buffer[current_offset:])
        current_offset += len(auth_output)
        segment_root_lookup, size = SegmentRootLookup.decode_from(buffer, current_offset)
        current_offset += size

        results = []
        while current_offset < len(buffer) and len(results) < MAX_WORK_ITEMS:
            result, size = WorkResult.decode_from(buffer, current_offset)
            results.append(result)
            current_offset += size

        if not results:
            raise ValueError("Work report must contain at least one result")

        return WorkReport(
            package_spec,
            context,
            core_index,
            authorizer_hash,
            auth_output,
            segment_root_lookup,
            results
        ), current_offset - offset
