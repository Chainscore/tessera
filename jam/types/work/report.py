"""Work report types for the JAM protocol."""
from dataclasses import dataclass
from enum import Enum
from typing import List, Any, Tuple, Sequence, Optional, Type, Union

from jam.types.base.choice import Choice
from jam.types.base.integers import U16, U32
from jam.types.base.bytes import Bytes
from jam.types.base.null import Null
from jam.types.base.vector import Vector
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ErasureRoot, ExportsRoot, WorkPackageHash
from jam.utils.codec.base import Codable

from jam.types.protocol.core import (
    ServiceId, Gas, CoreIndex
)
from jam.types.work.refine_context import RefineContext
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.codec.primitives.integers import GeneralCodec
from jam.utils.constants import MAX_WORK_ITEMS

class Ok(Bytes): pass
class OutOfGas(Null): pass
class Panic(Null): pass
class BadCode(Null): pass
class CodeOversize(Null): pass

class WorkExecResult(Codable):
    """Work execution result choice."""
    def __init__(self, value: Union[dict, Ok, OutOfGas, Panic, BadCode, CodeOversize]):
        self.types = [Ok, OutOfGas, Panic, BadCode, CodeOversize]
        if isinstance(value, dict):
            self.fromJson(value)
        else:
            self.set(value)
    
    """
    Examples:
        {
            "ok": "0xaabbcc"
            # "bad_code": null
            # "code_oversize": null
            # "panic": null
            # "out_of_gas": null
        }
    """
    def fromJson(self, json: dict):
        key = list(json.keys())[0]
        if key == "ok":
            self.set(Ok(json["ok"]))
        elif key == "bad_code":
            self.set(BadCode())
        elif key == "code_oversize":
            self.set(CodeOversize())
        elif key == "panic":
            self.set(Panic())
        elif key == "out_of_gas":
            self.set(OutOfGas())
        else:
            raise ValueError(f"Invalid key for WorkExecResult: {key}")

    def set(self, value: Codable):
        if not isinstance(value, (Bytes, Null)):
            raise ValueError(f"Invalid value for WorkExecResult: {value}")
        self.value = value
    
    def get(self) -> Codable:
        return self.value
    
    def encode_size(self) -> int:
        return GeneralCodec().encode_size(len(self.types)) + self.value.encode_size()

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        current_offset = offset
        tag = self.types.index(type(self.value))
        current_offset += GeneralCodec().encode_into(tag, buffer, current_offset)
        current_offset += self.value.encode_into(buffer, current_offset)
        return current_offset - offset

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0) -> Tuple[Any, int]:
        current_offset = offset
        result_type, size = GeneralCodec().decode_from(buffer, current_offset)
        current_offset += size
        if result_type == 0:
            result, size = Ok.decode_from(buffer, current_offset)
            result = Ok(result.data)
            current_offset += size
        elif result_type == 1:
            result = OutOfGas()
        elif result_type == 2:
            result = Panic()
        elif result_type == 3:
            result = BadCode()
        elif result_type == 4:
            result = CodeOversize()

        return WorkExecResult(result), current_offset - offset
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WorkExecResult):
            
            return self.value == other.value
        elif isinstance(other, dict):
            return self.value == WorkExecResult(other).value
        elif isinstance(other, Bytes) or isinstance(other, bytearray) or isinstance(other, bytes):
            return self.value == other
        elif other is None:
            return self.value == OutOfGas() or self.value == Panic() or self.value == BadCode() or self.value == CodeOversize()
        else:
            return False
        

@dataclass
class WorkResult(Codable):
    """Work result structure."""
    service_id: ServiceId
    code_hash: OpaqueHash
    payload_hash: OpaqueHash
    accumulate_gas: Gas
    result: WorkExecResult

    def enc_sequence(self) -> Sequence[Codable]:
        sequence = [
            self.service_id,
            self.code_hash,
            self.payload_hash,
            self.accumulate_gas,
            self.result
        ]
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
        service_id, size = ServiceId.decode_from(buffer, current_offset)
        current_offset += size
        code_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        payload_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        accumulate_gas, size = Gas.decode_from(buffer, current_offset)
        current_offset += size
        result, size = WorkExecResult.decode_from(buffer, current_offset)
        current_offset += size

        return WorkResult(
            service_id,
            code_hash,
            payload_hash,
            accumulate_gas,
            result
        ), current_offset - offset
    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WorkResult):
            print("Comparing", self.result.__class__.__name__, other.result.__class__.__name__, self.result == other.result)
            return self.service_id == other.service_id and self.code_hash == other.code_hash and self.payload_hash == other.payload_hash and self.accumulate_gas == other.accumulate_gas and self.result == other.result
        elif isinstance(other, dict):
            return self.service_id == other["service_id"] and self.code_hash == other["code_hash"] and self.payload_hash == other["payload_hash"] and self.accumulate_gas == other["accumulate_gas"] and self.result == other["result"]
        else:
            return False
    
    def __repr__(self) -> str:
        return f"WorkResult(service_id={self.service_id}, code_hash={self.code_hash}, payload_hash={self.payload_hash}, accumulate_gas={self.accumulate_gas}, result={self.result})"

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

@dataclass
class WorkReport(Codable):
    """Work report structure."""
    package_spec: WorkPackageSpec
    context: RefineContext
    core_index: CoreIndex
    authorizer_hash: OpaqueHash
    auth_output: Bytes
    segment_root_lookup: Vector[SegmentRootLookupItem]
    results: Vector[WorkResult]

    def __init__(self, package_spec: WorkPackageSpec,
                 context: RefineContext,
                 core_index: CoreIndex,
                 authorizer_hash: OpaqueHash,
                 auth_output: Bytes,
                 segment_root_lookup: Vector[SegmentRootLookupItem],
                 results: Vector[WorkResult]):
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
            self.segment_root_lookup,
            self.results
        ]
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
        auth_output, size = Bytes.decode_from(buffer, current_offset)
        current_offset += size
        segment_root_lookup, size = Vector.decode_from(SegmentRootLookupItem, buffer, current_offset)
        current_offset += size
        results, size = Vector.decode_from(WorkResult, buffer, current_offset)
        current_offset += size

        return WorkReport(
            package_spec,
            context,
            core_index,
            authorizer_hash,
            auth_output,
            Vector(segment_root_lookup),
            Vector(results)
        ), current_offset - offset

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, WorkReport):
            return self.package_spec == other.package_spec and self.context == other.context and self.core_index == other.core_index and self.authorizer_hash == other.authorizer_hash and self.auth_output == other.auth_output and self.segment_root_lookup == other.segment_root_lookup and self.results == other.results
        else:
            return False