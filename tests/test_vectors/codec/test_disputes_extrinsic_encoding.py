"""Tests for disputes extrinsic encoding."""
import json
from pathlib import Path

from jam.types.base.boolean import Boolean
from jam.types.base.vector import Vector
from jam.types.extrinsics.disputes import DisputesExtrinsic, Culprit, Fault, Judgement, JudgementVotes, Verdict
from jam.types.protocol.core import ValidatorIndex, WorkReportHash
from jam.types.protocol.crypto import Ed25519Public, Ed25519Signature
from jam.types.work import WorkReport, WorkPackageSpec
from jam.types.base.integers import U16, U32
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY

def test_disputes_extrinsic_encoding():
    """Test encoding/decoding of DisputesExtrinsic against test vectors."""
    test_dir = Path(__file__).parent / "data"
    
    # Load test vectors
    with open(test_dir / "disputes_extrinsic.json", "r") as f:
        disputes_json = json.load(f)
    
    with open(test_dir / "disputes_extrinsic.bin", "rb") as f:
        expected_bytes = f.read()

    # Create DisputesExtrinsic from JSON
    disputes = DisputesExtrinsic(
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
            ) for v in disputes_json["verdicts"]]
        ),
        culprits=Vector(
            [Culprit(
                target=WorkReportHash(c["target"]),
                key=Ed25519Public(c["key"]),
                signature=Ed25519Signature(c["signature"])
            ) for c in disputes_json["culprits"]]
        ),
        faults=Vector(
            [Fault(
                target=WorkReportHash(f["target"]),
                vote=Boolean(f["vote"]),
                key=Ed25519Public(bytes.fromhex(f["key"][2:])),
                signature=Ed25519Signature(bytes.fromhex(f["signature"][2:]))
            ) for f in disputes_json["faults"]]
        )
    )

    # Test encoding
    encoded = bytearray(disputes.encode_size())
    disputes.encode_into(encoded)
    assert disputes.encode_size() == len(expected_bytes)
    assert bytes(encoded) == expected_bytes

    # Test decoding
    decoded, size = DisputesExtrinsic.decode_from(expected_bytes)
    assert size == len(expected_bytes)
    assert decoded == disputes
