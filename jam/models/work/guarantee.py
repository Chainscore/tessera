from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.models.protocol.crypto import Ed25519Signature
from jam.models.protocol.core import TimeSlot, ValidatorIndex
from jam.models.work.report import WorkReport


@structure
class ValidatorSignature:
    """Validator signature structure."""

    validator_index: ValidatorIndex
    signature: Ed25519Signature


ValidatorSignatures = TypedVector[ValidatorSignature]


@structure
class ReportGuarantee:
    """Report guarantee structure."""

    report: WorkReport
    slot: TimeSlot
    signatures: ValidatorSignatures


GuaranteesExtrinsic = TypedVector[ReportGuarantee]
