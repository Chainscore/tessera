"""Extrinsic types for the JAM protocol."""

from jam.block.extrinsics.tickets import (
    TicketEnvelope,
    TicketsExtrinsic,
)

from jam.block.extrinsics.disputes import (
    Verdict,
    Culprit,
    Judgement,
    DisputesExtrinsic,
    Fault,
    DisputesRecords,
)

from jam.block.extrinsics.guarantees import (
    ValidatorSignature,
    ReportGuarantee,
    GuaranteesExtrinsic,
)

from jam.block.extrinsics.preimages import PreimagesExtrinsic

from jam.block.extrinsics.assurances import AssurancesExtrinsic

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
