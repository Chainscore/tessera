from jam.block import OffendersMark
from tsrkit_types.integers import U32

from jam.state.transitions import Disputes
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults, Verdict
from jam.types.protocol.crypto import WorkReportHash
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY
from jam.utils.dummy.utils import create_dummy_bytes32

from .data import (
    create_test_state,
    create_test_block,
    create_valid_judgement_votes,
    create_sorted_culprits,
    create_sorted_faults,
    deepcopy,
    get_state_counts,
    assert_state_counts,
    assert_targets_in_sets,
)


class TestProofOnlyTransitions:
    """Test culprit and fault proof only transitions"""

    def test_culprit_proofs_with_bad_verdict(self):
        """Test case 3a: Culprit proofs with bad verdict in same extrinsic"""
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Create initial state
        initial_state = create_test_state(tau=U32(0))

        # Create bad verdict
        bad_verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, False, VALIDATORS_SUPER_MAJORITY),
        )

        # Create culprit proofs for the bad verdict
        culprit_keys = [0, 1]
        culprits = create_sorted_culprits(target_hash, culprit_keys)

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([bad_verdict]), culprits=Culprits(culprits), faults=Faults([])
        )

        block = create_test_block(disputes_extrinsic)
        block.header.offenders_mark = OffendersMark.produce(disputes_extrinsic)

        initial_counts = get_state_counts(initial_state)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify target added to bad set and culprit keys added to offenders
        assert_state_counts(initial_counts, new_state, bad_delta=1, offenders_delta=2)
        assert_targets_in_sets(new_state, bad_targets=[target_hash], offender_keys=culprit_keys)

    def test_fault_proofs_only(self):
        """Test case 3b: Fault proofs only (for validators voting contrary to established verdicts)"""
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Create initial state with target already in good set
        initial_state = create_test_state(tau=U32(0), psi_good=[target_hash])

        # Create fault proofs for validators who voted against the good verdict
        fault_keys = [0, 1]
        faults = create_sorted_faults(
            target_hash, False, fault_keys
        )  # False vote contradicts good verdict

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([]), culprits=Culprits([]), faults=Faults(faults)
        )

        block = create_test_block(disputes_extrinsic)
        block.header.offenders_mark = OffendersMark.produce(disputes_extrinsic)

        initial_counts = get_state_counts(initial_state)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify fault keys added to offenders
        assert_state_counts(initial_counts, new_state, offenders_delta=2)
        assert_targets_in_sets(new_state, offender_keys=fault_keys)

        # Verify target remains in good set (unchanged)
        assert target_hash in new_state.psi.good
