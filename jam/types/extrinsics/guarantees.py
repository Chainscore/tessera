"""Guarantee-related extrinsic types for the JAM protocol."""
from dataclasses import dataclass
from jam.types.base import Vector
from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.crypto import Ed25519Signature
from jam.types.protocol.core import ValidatorIndex, TimeSlot
from jam.types.work import WorkReport
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass

@decodable_dataclass
@dataclass
class ValidatorSignature(Codable):
    """Validator signature structure."""
    validator_index: ValidatorIndex
    signature: Ed25519Signature

@decodable_vector(ValidatorSignature)
class ValidatorSignatures(Vector[ValidatorSignature]): ...

@decodable_dataclass
@dataclass
class ReportGuarantee(Codable):
    """Report guarantee structure."""
    report: WorkReport
    slot: TimeSlot
    signatures: ValidatorSignatures

@decodable_vector(ReportGuarantee)
class GuaranteesExtrinsic(Vector[ReportGuarantee]): ...
