"""Guarantee-related extrinsic types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Any, Tuple, Sequence, Union

from jam.types.base.integers import U16, U32
from jam.types.base.vector import Vector
from jam.utils.codec.base import Codable
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.protocol.core import ValidatorIndex, TimeSlot
from jam.types.work import WorkReport
from jam.utils.codec.composite.vectors import VectorCodec
from jam.utils.constants import CORE_COUNT

@dataclass
class ValidatorSignature(Codable):
    """Validator signature structure."""
    validator_index: ValidatorIndex
    signature: Ed25519Signature

    def enc_sequence(self) -> Sequence[Codable]:
        return [self.validator_index, self.signature]

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
        validator_index, size = ValidatorIndex.decode_from(buffer, current_offset)
        current_offset += size
        signature, size = Ed25519Signature.decode_from(buffer, current_offset)
        current_offset += size
        return ValidatorSignature(validator_index, signature), current_offset - offset

@dataclass
class ReportGuarantee(Codable):
    """Report guarantee structure."""
    report: WorkReport
    slot: TimeSlot
    signatures: Vector[ValidatorSignature]

    def enc_sequence(self) -> Sequence[Codable]:
        sequence: List[Codable] = [self.report, self.slot, self.signatures]
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
        report, size = WorkReport.decode_from(buffer, current_offset)
        current_offset += size
        slot, size = TimeSlot.decode_from(buffer, current_offset)
        current_offset += size
        signatures, size = Vector.decode_from(ValidatorSignature, buffer, current_offset)
        current_offset += size
        return ReportGuarantee(report, slot, Vector(signatures)), current_offset - offset

class GuaranteesExtrinsic(Vector[ReportGuarantee]):
    """Sequence of report guarantees with size limit of CORE_COUNT."""
    def __init__(self, guarantees: List[ReportGuarantee]):
        if len(guarantees) > CORE_COUNT:
            raise ValueError(f"Number of guarantees cannot exceed {CORE_COUNT}")
        super().__init__(guarantees)
    
    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray, memoryview], offset: int = 0):
        guarantees, size = VectorCodec.decode_from(ReportGuarantee, buffer, offset)
        return GuaranteesExtrinsic(guarantees), size
