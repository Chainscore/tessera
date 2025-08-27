from random import randint

from jam.block.extrinsics.extrinsic import Extrinsic
from jam.block.extrinsics.tickets import TicketEnvelope, TicketsExtrinsic
from jam.block.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.block.extrinsics.guarantees import (
    ReportGuarantee,
    ValidatorSignature,
    ValidatorSignatures,
    GuaranteesExtrinsic,
)
from jam.block.extrinsics.assurances import AvailAssurance, AssurancesExtrinsic
from jam.block.extrinsics.disputes import Verdicts, Culprits, Faults, DisputesExtrinsic
from jam.types.protocol.core import ServiceId, TimeSlot, ValidatorIndex, Gas
from tsrkit_types.integers import U32, U16, U8, Uint
from jam.types.work import WorkReport
from jam.types.work import (
    SegmentRootLookup,
    WorkPackageSpec,
    WorkDigest,
    WorkDigests,
    WorkExecResult,
    RefineLoad,
)
from jam.utils.dummy.utils import (
    create_dummy_bytes,
    create_dummy_bytes32,
    create_dummy_int,
)
from jam.types.work import RefineContext
from jam.types.protocol.crypto import Ed25519Signature, BandersnatchRingVrfSignature
from tsrkit_types.bytes import Bytes
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY


def create_dummy_package_spec() -> WorkPackageSpec:
    """Create dummy package spec"""
    return WorkPackageSpec(
        hash=create_dummy_bytes32(),
        length=U32(42),
        erasure_root=create_dummy_bytes32(),
        exports_root=create_dummy_bytes32(),
        exports_count=U16(69),
    )


def create_dummy_work_digest() -> WorkDigest:
    """Create dummy work result"""
    refine_load = RefineLoad(
        gas_used=Uint(0),
        imports=Uint(0),
        exports=Uint(0),
        extrinsic_count=Uint(0),
        extrinsic_size=Uint(0),
    )

    return WorkDigest(
        service_id=ServiceId(16909060),
        code_hash=create_dummy_bytes32(),
        payload_hash=create_dummy_bytes32(),
        accumulate_gas=Gas(42),
        result=WorkExecResult(Bytes(b"ok")),
        refine_load=refine_load,
    )


def create_dummy_work_report() -> WorkReport:
    """Create dummy work report"""
    return WorkReport(
        package_spec=create_dummy_package_spec(),
        context=RefineContext.empty(),
        core_index=Uint(3),
        authorizer_hash=create_dummy_bytes32(),
        auth_output=Bytes.fromhex("0102030405"),
        segment_root_lookup=SegmentRootLookup({}),
        results=WorkDigests([create_dummy_work_digest()]),
        auth_gas_used=Uint(0)
    )


def create_dummy_validator_signatures() -> list[ValidatorSignature]:
    """Create dummy validator signatures"""
    return [
        ValidatorSignature(
            validator_index=ValidatorIndex(i),
            signature=Ed25519Signature(create_dummy_bytes(64)),
        )
        for i in range(randint(2, 3))
    ]


def create_dummy_tickets(num=3) -> list[TicketEnvelope]:
    """Create dummy ticket.py"""
    return [
        TicketEnvelope(
            attempt=U8(i),
            signature=BandersnatchRingVrfSignature(create_dummy_bytes(784)),
        )
        for i in range(num)
    ]


def create_dummy_preimages(num=3) -> list[Preimage]:
    """Create dummy preimages"""
    return [
        Preimage.from_json(
            {
                "requester": create_dummy_int(32),
                "blob": create_dummy_bytes(create_dummy_int(12)).hex(),
            }
        )
        for _ in range(num)
    ]


def create_dummy_guarantees(num=3) -> list[ReportGuarantee]:
    """Create dummy guarantees"""
    return [
        ReportGuarantee(
            report=create_dummy_work_report(),
            slot=TimeSlot(42),
            signatures=ValidatorSignatures(create_dummy_validator_signatures()),
        )
        for _ in range(num)
    ]


def create_dummy_assurances(num=3) -> list[AvailAssurance]:
    """Create dummy assurances"""
    return [
        AvailAssurance.from_json(
            {
                "anchor": create_dummy_bytes32().hex(),
                "bitfield": "0x01",
                "validator_index": i,
                "signature": create_dummy_bytes(64).hex(),
            }
        )
        for i in range(num)
    ]


def create_dummy_disputes(num=3) -> DisputesExtrinsic:
    """Create dummy disputes"""
    return DisputesExtrinsic(
        verdicts=Verdicts.from_json(
            [
                {
                    "target": create_dummy_bytes(32).hex(),
                    "age": create_dummy_int(32),
                    "votes": [
                        {
                            "vote": True,
                            "index": 0,
                            "signature": create_dummy_bytes(64).hex(),
                        }
                        for _ in range(VALIDATORS_SUPER_MAJORITY)
                    ],
                }
                for _ in range(num)
            ]
        ),
        culprits=Culprits.from_json(
            [
                {
                    "target": create_dummy_bytes(32).hex(),
                    "key": create_dummy_bytes(32).hex(),
                    "signature": create_dummy_bytes(64).hex(),
                }
                for _ in range(num)
            ]
        ),
        faults=Faults.from_json(
            [
                {
                    "target": create_dummy_bytes(32).hex(),
                    "vote": True,
                    "key": create_dummy_bytes(32).hex(),
                    "signature": create_dummy_bytes(64).hex(),
                }
                for _ in range(0)
            ]
        ),
    )


def create_dummy_extrinsics(n_et=3, n_ep=3, n_ea=3, n_eg=3, n_ed=3) -> Extrinsic:
    """Create dummy extrinsics"""
    return Extrinsic(
        tickets=TicketsExtrinsic(create_dummy_tickets(n_et)),
        preimages=PreimagesExtrinsic(create_dummy_preimages(n_ep)),
        guarantees=GuaranteesExtrinsic(create_dummy_guarantees(n_eg)),
        assurances=AssurancesExtrinsic(create_dummy_assurances(n_ea)),
        disputes=create_dummy_disputes(n_ed),
    )
