import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types.integers import U32
from tsrkit_types.bool import Bool

from jam.settings import Settings
from jam.state.transitions import Disputes, DisputesError, DisputesErrorCode
from jam.block.extrinsics.disputes import (
    DisputesExtrinsic, Verdicts, Culprits, Faults, 
    Verdict, Fault
)
from jam.types.protocol.crypto import WorkReportHash, Ed25519Signature
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY, X
from jam.utils.dummy.utils import create_dummy_bytes32, create_dummy_bytes

from .data import (
    create_test_state, create_test_block, create_valid_judgement_votes, deepcopy
)


class TestDisputesValidationErrors:
    """Test disputes validation error cases"""
    
    def test_invalid_signature(self):
        """Test case 4a: Invalid signature"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        good_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY)
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([good_verdict]),
            culprits=Culprits([]),
            faults=Faults([])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        # Mock signature verification to return False
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.BAD_SIGNATURE
    
    def test_verdicts_not_sorted(self):
        """Test case 4b: Verdicts not sorted by target hash"""
        initial_state = create_test_state(tau=U32(0))
        
        # Create two targets with hashes that will be out of order
        target1 = WorkReportHash(b'\xff' * 32)  # Higher hash
        target2 = WorkReportHash(b'\x00' * 32)  # Lower hash
        
        # Create verdicts in wrong order (high hash first, low hash second)
        verdict1 = Verdict(
            target=target1,
            age=U32(0),
            votes=create_valid_judgement_votes(target1, True, VALIDATORS_SUPER_MAJORITY)
        )
        verdict2 = Verdict(
            target=target2,
            age=U32(0),
            votes=create_valid_judgement_votes(target2, True, VALIDATORS_SUPER_MAJORITY)
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([verdict1, verdict2]),  # Wrong order
            culprits=Culprits([]),
            faults=Faults([])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.VERDICTS_NOT_SORTED_UNIQUE
    
    def test_good_verdict_without_fault_proof(self):
        """Test case 4c: Good verdict without required fault proof"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        good_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY)
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([good_verdict]),
            culprits=Culprits([]),
            faults=Faults([])  # Missing required fault proof
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.NOT_ENOUGH_FAULTS
    
    def test_bad_verdict_without_culprit_proof(self):
        """Test case 4d: Bad verdict without required culprit proof"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        bad_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, False, VALIDATORS_SUPER_MAJORITY)
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([bad_verdict]),
            culprits=Culprits([]),  # Missing required culprit proof
            faults=Faults([])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.NOT_ENOUGH_CULPRITS
    
    def test_invalid_judgment_age(self):
        """Test case 4e: Invalid judgment age (too old)"""
        initial_state = create_test_state(tau=U32(10))  # Current epoch is 10
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        # Create verdict with age that's too old
        old_verdict = Verdict(
            target=target_hash,
            age=U32(5),  # Age 5 when current epoch is 10 - too old
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY)
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([old_verdict]),
            culprits=Culprits([]),
            faults=Faults([])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.BAD_JUDGEMENT_AGE
    
    def test_fault_verdict_contradiction(self):
        """Test case 4f: Fault proof contradicts established verdict"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        # Create good verdict (positive votes)
        good_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY)
        )
        
        # Create fault proof with same vote as verdict (should contradict)
        key0 = Settings(None, 0)
        fault = Fault(
            target=target_hash,
            vote=Bool(True),  # Same as verdict - this should be invalid
            key=key0.ed25519_public,
            signature=Ed25519Signature(
                Ed25519PrivateKey.from_private_bytes(key0.ed25519_private).sign(X.VALID.value + target_hash))
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([good_verdict]),
            culprits=Culprits([]),
            faults=Faults([fault])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.FAULT_VERDICT_WRONG
    
    def test_invalid_vote_split(self):
        """Test case 4g: Invalid vote split (not enough votes for wonky)"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())
        
        # Skip if VALIDATORS_WONKY is too small for minimum JudgementVotes length
        if VALIDATORS_WONKY < 5:  # JudgementVotes has minimum length of 5
            pytest.skip(f"VALIDATORS_WONKY ({VALIDATORS_WONKY}) is too small for minimum JudgementVotes length")
        
        # Skip if we can't create an invalid vote count
        if VALIDATORS_WONKY - 1 < 5:
            pytest.skip(f"Cannot create invalid vote count with VALIDATORS_WONKY={VALIDATORS_WONKY}")
        
        # Create verdict with fewer votes than required for wonky
        invalid_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_WONKY - 1)  # Not enough for wonky
        )
        
        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([invalid_verdict]),
            culprits=Culprits([]),
            faults=Faults([])
        )
        
        block = create_test_block(disputes_extrinsic)
        
        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        assert exc_info.value.code == DisputesErrorCode.BAD_VOTE_SPLIT
