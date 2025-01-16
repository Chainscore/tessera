"""Work report types for the JAM protocol."""
from dataclasses import dataclass
from typing import Any, Tuple, Union

from jam.types.base.integers import U16, U32
from jam.types.base.bytes import Bytes
from jam.types.base.null import Null
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ErasureRoot, ExportsRoot, WorkPackageHash
from jam.utils.codec import Codable, decodable_dataclass

from jam.types.protocol.core import (
    ServiceId, Gas, CoreIndex
)
from jam.types.work.refine_context import RefineContext
from jam.utils.codec.primitives.integers import GeneralCodec

class Ok(Bytes): ...
class OutOfGas(Null): ...
class Panic(Null): ...
class BadCode(Null): ...
class CodeOversize(Null): ...


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
            self.set(Ok(Bytes(json["ok"])))
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
            result = Ok(result.value)
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
        

@decodable_dataclass
@dataclass
class WorkResult(Codable):
    """Work result structure."""
    service_id: ServiceId
    code_hash: OpaqueHash
    payload_hash: OpaqueHash
    accumulate_gas: Gas
    result: WorkExecResult

@decodable_dataclass
@dataclass
class WorkPackageSpec(Codable):
    """Work package specification structure."""
    hash: WorkPackageHash
    length: U32
    erasure_root: ErasureRoot
    exports_root: ExportsRoot
    exports_count: U16

@decodable_dataclass
@dataclass
class SegmentRootLookupItem(Codable):
    """Segment root lookup item structure."""
    work_package_hash: WorkPackageHash
    segment_tree_root: OpaqueHash

@decodable_vector(SegmentRootLookupItem)
class SegmentRootLookup(Vector[SegmentRootLookupItem]): ...

@decodable_vector(WorkResult)
class WorkResults(Vector[WorkResult]): ...

@decodable_dataclass
@dataclass
class WorkReport(Codable):
    """Work report structure."""
    package_spec: WorkPackageSpec
    context: RefineContext
    core_index: CoreIndex
    authorizer_hash: OpaqueHash
    auth_output: Bytes
    segment_root_lookup: SegmentRootLookup
    results: WorkResults