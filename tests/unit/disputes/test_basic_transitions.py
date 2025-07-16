from jam.settings import Settings
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tsrkit_types.integers import U32, U8
from tsrkit_types.bool import Bool

from jam.state.transitions import Disputes
from jam.block.extrinsics.disputes import (
    DisputesExtrinsic,
    Verdicts,
    Culprits,
    Faults,
    Verdict,
    Culprit,
    Fault,
)
from jam.types.protocol.crypto import Ed25519Public, Ed25519Signature, WorkReportHash
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY, X
from jam.utils.dummy.utils import create_dummy_bytes, create_dummy_bytes32

from .data import (
    create_test_state,
    create_test_block,
    create_valid_judgement_votes,
    create_sorted_culprits,
    deepcopy,
    get_state_counts,
    assert_state_counts,
    assert_targets_in_sets,
)


class TestBasicDisputesTransitions:
    """Test basic disputes transitions"""

    def test_empty_disputes_extrinsic(self):
        """Test case 1: No Disputes Extrinsic (ED empty)"""
        # Create initial state with some existing dispute records
        initial_good = [WorkReportHash(create_dummy_bytes32())]
        initial_bad = [WorkReportHash(create_dummy_bytes32())]
        initial_wonky = [WorkReportHash(create_dummy_bytes32())]
        initial_offenders = [Ed25519Public(create_dummy_bytes32())]

        initial_state = create_test_state(
            psi_good=initial_good,
            psi_bad=initial_bad,
            psi_wonky=initial_wonky,
            psi_offenders=initial_offenders,
        )

        # Create block with empty disputes extrinsic
        block = create_test_block(
            DisputesExtrinsic(verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults([]))
        )

        # Apply transition
        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify all dispute records remain unchanged
        assert new_state.psi.good == initial_state.psi.good
        assert new_state.psi.bad == initial_state.psi.bad
        assert new_state.psi.wonky == initial_state.psi.wonky
        assert new_state.psi.offenders == initial_state.psi.offenders
        assert new_state.rho == initial_state.rho

    def test_good_verdict_only(self):
        """Test case 2a: Good verdict (all positive votes with super majority)"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Store initial counts
        initial_counts = get_state_counts(initial_state)

        # Create good verdict with super majority positive votes
        good_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY),
        )

        # Create at least one fault as required for good verdicts
        key0 = Settings(None, 0)
        fault = Fault(
            target=target_hash,
            vote=Bool(False),  # Contradicting the good verdict
            key=key0.ed25519_public,
            signature=Ed25519Signature(
                Ed25519Signature(
                    Ed25519PrivateKey.from_private_bytes(key0.ed25519_private).sign(
                        X.INVALID.value + target_hash
                    )
                )
            ),
        )

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([good_verdict]), culprits=Culprits([]), faults=Faults([fault])
        )

        block = create_test_block(disputes_extrinsic)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify changes using helper functions
        assert_state_counts(initial_counts, new_state, good_delta=1, offenders_delta=1)
        assert_targets_in_sets(new_state, good_targets=[target_hash], offender_keys=[0])

    def test_bad_verdict_only(self):
        """Test case 2b: Bad verdict (all negative votes)"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Store initial counts
        initial_counts = get_state_counts(initial_state)

        # Create bad verdict with all negative votes
        bad_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, False, VALIDATORS_SUPER_MAJORITY),
        )

        # Create at least two culprits as required for bad verdicts
        culprit_keys = [0, 1]
        culprits = create_sorted_culprits(target_hash, culprit_keys)

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([bad_verdict]), culprits=Culprits(culprits), faults=Faults([])
        )

        block = create_test_block(disputes_extrinsic)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify changes using helper functions
        assert_state_counts(initial_counts, new_state, bad_delta=1, offenders_delta=2)
        assert_targets_in_sets(new_state, bad_targets=[target_hash], offender_keys=culprit_keys)

    def test_wonky_verdict_only(self):
        """Test case 2c: Wonky verdict (exactly VALIDATORS_WONKY positive votes)"""
        initial_state = create_test_state(tau=U32(0))
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Create wonky verdict with exactly VALIDATORS_WONKY positive votes
        wonky_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY),
        )

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([wonky_verdict]), culprits=Culprits([]), faults=Faults([])
        )

        block = create_test_block(disputes_extrinsic)

        initial_counts = get_state_counts(initial_state)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify changes using helper functions
        assert_state_counts(initial_counts, new_state, wonky_delta=1)
        assert_targets_in_sets(new_state, wonky_targets=[target_hash])
