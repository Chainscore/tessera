"""Tests for block encoding."""
import json
from pathlib import Path

from jam.types.base.boolean import Boolean
from jam.types.base.integers import U16, U32
from jam.types.base import Vector
from jam.types.block import Block, Header, Extrinsic
from jam.types.base import Bytes
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


    block = Block.from_json(block_json)

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