"""Work item types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence

from jam.types.base.integers import U16, U32
from jam.types.base.bytes import Bytes
from jam.types.base.vector import Vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import OpaqueHash
from jam.types.protocol.core import ServiceId, Gas

@dataclass
class ImportSpec(Codable):
    """Import specification structure."""
    tree_root: OpaqueHash
    index: U16

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.tree_root, self.index]

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
        tree_root, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        index, size = U16.decode_from(buffer, current_offset)
        current_offset += size
        return ImportSpec(tree_root, index), current_offset - offset

@dataclass
class ExtrinsicSpec(Codable):
    """Extrinsic specification structure."""
    hash: OpaqueHash
    len: U32

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.hash, self.len]

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
        hash_val, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        len_val, size = U32.decode_from(buffer, current_offset)
        current_offset += size
        return ExtrinsicSpec(hash_val, len_val), current_offset - offset

@dataclass
class WorkItem(Codable):
    """Work item structure."""
    service: ServiceId
    code_hash: OpaqueHash
    payload: Bytes
    refine_gas_limit: Gas
    accumulate_gas_limit: Gas
    import_segments: Vector[ImportSpec]
    extrinsic: Vector[ExtrinsicSpec]
    export_count: U16

    def enc_sequence(self) -> Sequence[Codable]:
        sequence: List[Codable] = [
            self.service,
            self.code_hash,
            self.payload,
            self.refine_gas_limit,
            self.accumulate_gas_limit,
            self.import_segments,
            self.extrinsic,
            self.export_count
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
        service, size = ServiceId.decode_from(buffer, current_offset)
        current_offset += size
        code_hash, size = OpaqueHash.decode_from(buffer, current_offset)
        current_offset += size
        payload, size = Bytes.decode_from(buffer, current_offset)
        current_offset += size
        refine_gas_limit, size = Gas.decode_from(buffer, current_offset)
        current_offset += size
        accumulate_gas_limit, size = Gas.decode_from(buffer, current_offset)
        current_offset += size
        import_segments, size = Vector.decode_from(ImportSpec, buffer, current_offset)
        current_offset += size
        extrinsic, size = Vector.decode_from(ExtrinsicSpec, buffer, current_offset)
        current_offset += size
        export_count, size = U16.decode_from(buffer, current_offset)
        current_offset += size

        return WorkItem(
            service,
            code_hash,
            payload,
            refine_gas_limit,
            accumulate_gas_limit,
            Vector(import_segments),
            Vector(extrinsic),
            export_count
        ), current_offset - offset
