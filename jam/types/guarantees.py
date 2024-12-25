"""Guarantee types for the JAM protocol."""
from dataclasses import dataclass
from typing import List
from .base import U32
from .core import ValidatorIndex, TimeSlot
from .crypto import Ed25519Signature
from .work import WorkReport

@dataclass
class ValidatorSignature:
    """Validator signature structure."""
    validator_index: ValidatorIndex
    signature: Ed25519Signature

@dataclass
class ReportGuarantee:
    """Report guarantee structure."""
    report: WorkReport
    slot: TimeSlot
    signatures: List[ValidatorSignature]

@dataclass
class GuaranteesExtrinsic:
    """Guarantees extrinsic structure."""
    guarantees: List[ReportGuarantee]

    def __post_init__(self):
        # cores_count should be imported from constants
        if len(self.guarantees) > 0:  # cores_count
            raise ValueError("GuaranteesExtrinsic exceeds cores count") 