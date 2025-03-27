from jam.types import (
    Ed25519Signature,
    BandersnatchRingVrfSignature,
    TimeSlot,
    WorkResult,
    WorkExecResult,
    RefineContext,
    WorkPackageSpec,
    Bytes,
)
from jam.types.block import Extrinsic
from jam.types.extrinsics import (
    TicketsExtrinsic,
    PreimagesExtrinsic,
    GuaranteesExtrinsic,
    AssurancesExtrinsic,
    DisputesExtrinsic,
)
from jam.types.extrinsics.tickets import TicketEnvelope
from jam.types.extrinsics.preimages import Preimage
from jam.types.extrinsics.guarantees import ReportGuarantee, ValidatorSignature, ValidatorSignatures
from jam.types.extrinsics.assurances import AvailAssurance, AvailBitField
from jam.types.extrinsics.disputes import Verdicts, Culprits, Faults, Judgement
from jam.types.protocol.core import ServiceId, ValidatorIndex, Gas
from jam.types.base.boolean import Boolean
from jam.types.base.integers.fixed import U32, U16, U8
from jam.types.work import WorkReport
from jam.types.work.report import SegmentRootLookup, WorkResults
from tests.fixtures.utils import create_dummy_bytes, create_dummy_bytes32
from jam.types.work.refine_context import OpaqueHashes
from jam.types.protocol.crypto import OpaqueHash



def create_dummy_package_spec() -> WorkPackageSpec:
    """Create dummy package spec"""
    return WorkPackageSpec(
        hash=create_dummy_bytes32(),
        length=U32(42),
        erasure_root=create_dummy_bytes32(),
        exports_root=create_dummy_bytes32(),
        exports_count=U16(69),
    )


def create_dummy_work_context() -> RefineContext:
    """Create dummy work context"""
    return RefineContext(
        anchor=create_dummy_bytes32(),
        state_root=create_dummy_bytes32(),
        beefy_root=create_dummy_bytes32(),
        lookup_anchor=create_dummy_bytes32(),
        lookup_anchor_slot=TimeSlot(33),
        prerequisites=OpaqueHashes([]),
    )


def create_dummy_work_result() -> WorkResult:
    """Create dummy work result"""
    return WorkResult(
        service_id=ServiceId(16909060),
        code_hash=create_dummy_bytes32(),
        payload_hash=create_dummy_bytes32(),
        accumulate_gas=Gas(42),
        result=WorkExecResult({"ok": Bytes(create_dummy_bytes(16))}),
    )


def create_dummy_work_report() -> WorkReport:
    """Create dummy work report"""
    return WorkReport(
        package_spec=create_dummy_package_spec(),
        context=create_dummy_work_context(),
        core_index=U16(3),
        authorizer_hash=create_dummy_bytes32(),
        auth_output=Bytes("0x0102030405"),
        segment_root_lookup=SegmentRootLookup([]),
        results=WorkResults([create_dummy_work_result()]),
    )


def create_dummy_validator_signatures() -> list[ValidatorSignature]:
    """Create dummy validator signatures"""
    return [
        ValidatorSignature(
            validator_index=ValidatorIndex(i),
            signature=Ed25519Signature(create_dummy_bytes(64)),
        )
        for i in range(2)
    ]


def create_dummy_tickets() -> list[TicketEnvelope]:
    """Create dummy tickets"""
    return [
        TicketEnvelope(
            attempt=U8(i), signature=BandersnatchRingVrfSignature(create_dummy_bytes(784))
        )
        for i in range(3)
    ]


def create_dummy_preimages() -> list[Preimage]:
    """Create dummy preimages"""
    return [
        Preimage(requester=ServiceId(16909060 + i), blob=Bytes(create_dummy_bytes(16)))
        for i in range(3)
    ]


def create_dummy_guarantees() -> list[ReportGuarantee]:
    """Create dummy guarantees"""
    return [
        ReportGuarantee(
            report=create_dummy_work_report(),
            slot=TimeSlot(42),
            signatures=ValidatorSignatures(create_dummy_validator_signatures()),
        )
    ]


def create_dummy_assurances() -> list[AvailAssurance]:
    """Create dummy assurances"""
    return [
        AvailAssurance(
            anchor=OpaqueHash(create_dummy_bytes32()),
            bitfield=AvailBitField("0x01"),
            validator_index=ValidatorIndex(i),
            signature=Ed25519Signature(create_dummy_bytes(64)),
        )
        for i in range(2)
    ]

def create_dummy_disputes() -> DisputesExtrinsic:
    """Create dummy disputes"""
    return DisputesExtrinsic(
        verdicts=Verdicts([]),
        culprits=Culprits([]),
        faults=Faults([]),
    )


def create_dummy_extrinsics() -> Extrinsic:
    """Create dummy extrinsics"""
    return Extrinsic(
        tickets=TicketsExtrinsic(create_dummy_tickets()),
        preimages=PreimagesExtrinsic(create_dummy_preimages()),
        guarantees=GuaranteesExtrinsic(create_dummy_guarantees()),
        assurances=AssurancesExtrinsic(create_dummy_assurances()),
        disputes=create_dummy_disputes(),
    )
