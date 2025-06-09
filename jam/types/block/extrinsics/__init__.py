"""Extrinsic types for the JAM protocol."""

from jam.types.block.extrinsics.tickets import (
    TicketEnvelope,
    TicketsExtrinsic,
)

from jam.types.block.extrinsics.disputes import (
    Verdict,
    Culprit,
    Judgement,
    DisputesExtrinsic,
    Fault,
    DisputesRecords,
)

from jam.types.block.extrinsics.guarantees import (
    ValidatorSignature,
    ReportGuarantee,
    GuaranteesExtrinsic,
)

from jam.types.block.extrinsics.preimages import PreimagesExtrinsic

from jam.types.block.extrinsics.assurances import AssurancesExtrinsic

__all__ = [
    # Ticket types
    "TicketEnvelope",
    "TicketsExtrinsic",
    # Dispute types
    "Verdict",
    "Culprit",
    "Judgement",
    "DisputesExtrinsic",
    "Fault",
    "DisputesRecords",
    # Guarantee types
    "ValidatorSignature",
    "ReportGuarantee",
    "GuaranteesExtrinsic",
    # Preimage types
    "PreimagesExtrinsic",
    # Assurance types
    "AssurancesExtrinsic",
]
