"""Tests for block encoding."""
import json
from pathlib import Path

from jam.types.base.boolean import Boolean
from jam.types.base.integers import U16, U32
from jam.types.base import Vector
from jam.types.block import Block, Header, Extrinsic
from jam.types.base.bytes import Bytes
from jam.types.extrinsics.assurances import AssurancesExtrinsic, AvailAssurance, AvailBitField
from jam.types.extrinsics.disputes import Culprit, DisputesExtrinsic, Fault, Judgement, JudgementVotes, Verdict
from jam.types.extrinsics.guarantees import GuaranteesExtrinsic, ReportGuarantee, ValidatorSignature
from jam.types.extrinsics.preimages import Preimage, PreimagesExtrinsic
from jam.types.protocol.core import CoreIndex, ErasureRoot, ExportsRoot, Gas, ServiceId, TimeSlot, ValidatorIndex, WorkReportHash
from jam.types.protocol.crypto import (
    BandersnatchRingVrfSignature, BeefyRoot, Ed25519Public, Ed25519Signature, Entropy, HeaderHash, StateRoot, OpaqueHash,
    BandersnatchPublic, BandersnatchVrfSignature
)
from jam.types.protocol.epoch import EpochMark
from jam.types.protocol.validators import ValidatorArray
from jam.types.header import OffendersMark, TicketsMark
from jam.types.extrinsics.tickets import TicketAttempt, TicketBody, TicketEnvelope, TicketId, TicketsExtrinsic
from jam.types.work.refine_context import RefineContext
from jam.types.work.report import SegmentRootLookupItem, WorkExecResult, WorkPackageSpec, WorkReport, WorkResult

def test_block_encoding():
    """Test encoding/decoding of Block against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "block.json", "r") as f:
        block_json = json.load(f)
    
    with open(test_dir / "block.bin", "rb") as f:
        expected_bytes = f.read()

    # Create Block from JSON
    epoch_mark = None
    tickets_mark = None
    if block_json["header"]["epoch_mark"] is not None:
        epoch_mark = EpochMark(
            entropy=Entropy(bytes.fromhex(block_json["header"]["epoch_mark"]["entropy"][2:])),
            tickets_entropy=Entropy(bytes.fromhex(block_json["header"]["epoch_mark"]["tickets_entropy"][2:])),
            validators=ValidatorArray(
                [BandersnatchPublic(bytes.fromhex(validator[2:])) for validator in block_json["header"]["epoch_mark"]["validators"]]
            )
        )
    if block_json["header"]["tickets_mark"] is not None:
        tickets_mark = TicketsMark(
            [TicketBody(TicketId(bytes.fromhex(ticket['id'][2:])), TicketAttempt(int(ticket['attempt']))) for ticket in block_json["header"]["tickets_mark"]]
        )

    header = Header(
        parent=HeaderHash(bytes.fromhex(block_json["header"]["parent"][2:])),
        parent_state_root=StateRoot(bytes.fromhex(block_json["header"]["parent_state_root"][2:])),
        extrinsic_hash=OpaqueHash(bytes.fromhex(block_json["header"]["extrinsic_hash"][2:])),
        slot=TimeSlot(block_json["header"]["slot"]),
        epoch_mark=epoch_mark,
        tickets_mark=tickets_mark,
        offenders_mark=OffendersMark(
            [Ed25519Public(bytes.fromhex(offender[2:])) for offender in block_json["header"]["offenders_mark"]]
        ),
        author_index=ValidatorIndex(block_json["header"]["author_index"]),
        entropy_source=BandersnatchVrfSignature(bytes.fromhex(block_json["header"]["entropy_source"][2:])),
        seal=BandersnatchVrfSignature(bytes.fromhex(block_json["header"]["seal"][2:]))
    )

    block = Block(
        header=header,
        extrinsic=Extrinsic(
            tickets=TicketsExtrinsic([TicketEnvelope(
                attempt=TicketAttempt(int(ticket["attempt"])),
                signature=BandersnatchRingVrfSignature(ticket["signature"])
            ) for ticket in block_json["extrinsic"]["tickets"]]),
            preimages=PreimagesExtrinsic([Preimage(
                requester=ServiceId(int(preimage["requester"])),
                blob=Bytes(preimage["blob"])
            ) for preimage in block_json["extrinsic"]["preimages"]]),
            guarantees=GuaranteesExtrinsic(
        [ReportGuarantee(
            report=WorkReport(
                package_spec=WorkPackageSpec(
                    hash=OpaqueHash(bytes.fromhex(g["report"]["package_spec"]["hash"][2:])),
                    length=U32(g["report"]["package_spec"]["length"]),
                    erasure_root=ErasureRoot(bytes.fromhex(g["report"]["package_spec"]["erasure_root"][2:])),
                    exports_root=ExportsRoot(bytes.fromhex(g["report"]["package_spec"]["exports_root"][2:])),
                    exports_count=U16(g["report"]["package_spec"]["exports_count"])
                ),
                context=RefineContext(
                    anchor=HeaderHash(g["report"]["context"]["anchor"]),
                    state_root=StateRoot(g["report"]["context"]["state_root"]),
                    beefy_root=BeefyRoot(g["report"]["context"]["beefy_root"]),
                    lookup_anchor=HeaderHash(g["report"]["context"]["lookup_anchor"]),
                    lookup_anchor_slot=TimeSlot(g["report"]["context"]["lookup_anchor_slot"]),
                    prerequisites=Vector(
                        [OpaqueHash(p) for p in g["report"]["context"]["prerequisites"]]
                    )
                ),
                core_index=CoreIndex(g["report"]["core_index"]),
                authorizer_hash=OpaqueHash(g["report"]["authorizer_hash"]),
                auth_output=Bytes(g["report"]["auth_output"]),
                segment_root_lookup=Vector([SegmentRootLookupItem(
                    work_package_hash=OpaqueHash(g["report"]["segment_root_lookup"]["work_package_hash"]),
                    segment_tree_root=OpaqueHash(g["report"]["segment_root_lookup"]["segment_tree_root"])
                ) for s in g["report"]["segment_root_lookup"]]),
                results=Vector([WorkResult(
                    service_id=ServiceId(r["service_id"]),
                    code_hash=OpaqueHash(r["code_hash"]),
                    payload_hash=OpaqueHash(r["payload_hash"]),
                    accumulate_gas=Gas(r["accumulate_gas"]),
                    result=WorkExecResult(r["result"])
                ) for r in g["report"]["results"]])
            ),
            slot=TimeSlot(g["slot"]),
            signatures=Vector(
                [ValidatorSignature(
                    validator_index=ValidatorIndex(s["validator_index"]),
                    signature=Ed25519Signature(bytes.fromhex(s["signature"][2:]))
                ) for s in g["signatures"]]
            )
        ) for g in block_json["extrinsic"]["guarantees"]]),
        assurances=AssurancesExtrinsic([AvailAssurance(
            anchor=HeaderHash(assurance["anchor"]),
            bitfield=AvailBitField(assurance["bitfield"]),
            validator_index=ValidatorIndex(assurance["validator_index"]),
            signature=Ed25519Signature(bytes.fromhex(assurance["signature"][2:]))
            ) for assurance in block_json["extrinsic"]["assurances"]]),
        disputes=DisputesExtrinsic(
        verdicts=Vector(
            [Verdict(
                target=WorkReportHash(v["target"]),
                age=U32(v["age"]),
                votes=JudgementVotes(
                    [Judgement(
                        vote=Boolean(j["vote"]),
                        index=ValidatorIndex(j["index"]),
                        signature=Ed25519Signature(j["signature"])
                    ) for j in v["votes"]]
                )
            ) for v in block_json["extrinsic"]["disputes"]["verdicts"]]
        ),
        culprits=Vector(
            [Culprit(
                target=WorkReportHash(c["target"]),
                key=Ed25519Public(c["key"]),
                signature=Ed25519Signature(c["signature"])
            ) for c in block_json["extrinsic"]["disputes"]["culprits"]]
        ),
        faults=Vector(
            [Fault(
                target=WorkReportHash(f["target"]),
                vote=Boolean(f["vote"]),
                key=Ed25519Public(bytes.fromhex(f["key"][2:])),
                signature=Ed25519Signature(bytes.fromhex(f["signature"][2:]))
            ) for f in block_json["extrinsic"]["disputes"]["faults"]]
        )
        )
    ))

    # Test encoding
    encoded = bytearray(block.encode_size())
    block.encode_into(encoded)
    assert bytes(encoded) == expected_bytes
    assert block.encode_size() == len(expected_bytes)

    # Test decoding
    decoded, size = Block.decode_from(expected_bytes)
    # assert size == len(expected_bytes)
    
    # Verify decoded matches original
    assert decoded.header == block.header
    assert decoded.extrinsic == block.extrinsic
    # assert decoded == block