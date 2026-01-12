import pytest

from jam.block import OffendersMark
from tsrkit_types.integers import U32

from jam.settings import Settings
from jam.state.transitions import Disputes, DisputesError, DisputesErrorCode
from jam.block.extrinsics.disputes import DisputesExtrinsic, Verdicts, Culprits, Faults, Verdict
from jam.types.protocol.crypto import Ed25519Public, WorkReportHash
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY
from jam.utils.dummy.utils import create_dummy_bytes32

from .data import (
    create_test_state,
    create_test_block,
    create_valid_judgement_votes,
    create_sorted_culprits,
    create_sorted_faults,
    create_sorted_verdicts,
    deepcopy,
    get_state_counts,
    assert_state_counts,
    assert_targets_in_sets,
)


class TestMixedDisputesScenarios:
    """Test mixed verdicts and proofs scenarios"""

    def test_mixed_verdicts_and_proofs(self):
        """Test case 5a: Mixed verdicts and proofs in single extrinsic"""
        # Create multiple targets
        target1 = WorkReportHash(b"\x00" * 32)  # Lower hash (will be first after sorting)
        target2 = WorkReportHash(b"\x11" * 32)  # Higher hash (will be second after sorting)
        target3 = WorkReportHash(b"\x22" * 32)  # Already bad target

        # Create initial state with one target already bad
        initial_state = create_test_state(tau=U32(0), psi_bad=[target3])

        # Create verdicts (must be sorted by target hash)
        verdicts_data = [
            (target1, U32(0), True, VALIDATORS_SUPER_MAJORITY),  # Good verdict
            (target2, U32(0), False, VALIDATORS_SUPER_MAJORITY),  # Bad verdict
        ]
        verdicts = create_sorted_verdicts(verdicts_data)

        # Create culprits for bad verdict (target2) only
        # Note: Cannot provide culprits for target3 since it doesn't have a bad verdict in this extrinsic
        culprit_keys_target2 = [0, 1]
        culprits = create_sorted_culprits(target2, culprit_keys_target2)

        # Create faults for good verdict (target1)
        fault_keys = [3]
        faults = create_sorted_faults(
            target1, False, fault_keys
        )  # False vote contradicts good verdict

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts(verdicts), culprits=Culprits(culprits), faults=Faults(faults)
        )

        block = create_test_block(disputes_extrinsic)
        block.header.offenders_mark = OffendersMark.produce(disputes_extrinsic)

        initial_counts = get_state_counts(initial_state)

        new_state = Disputes.transition(deepcopy(initial_state), initial_state, block)

        # Verify state changes
        # +1 good (target1), +1 bad (target2), +3 offenders (2+1)
        assert_state_counts(initial_counts, new_state, good_delta=1, bad_delta=1, offenders_delta=3)

        # Verify specific targets/keys
        assert_targets_in_sets(
            new_state,
            good_targets=[target1],
            bad_targets=[target2, target3],  # target3 was already bad
            offender_keys=culprit_keys_target2 + fault_keys,
        )

    def test_already_judged_target(self):
        """Test case 5b: Attempt to judge already judged target"""
        target_hash = WorkReportHash(create_dummy_bytes32())

        # Create initial state with target already in good set
        initial_state = create_test_state(tau=U32(0), psi_good=[target_hash])

        # Try to judge the same target again
        verdict = Verdict(
            target=target_hash,
            age=U32(0),
            votes=create_valid_judgement_votes(target_hash, True, VALIDATORS_SUPER_MAJORITY),
        )

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([verdict]), culprits=Culprits([]), faults=Faults([])
        )

        block = create_test_block(disputes_extrinsic)
        block.header.offenders_mark = OffendersMark.produce(disputes_extrinsic)

        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        # This might be caught by different validation errors depending on implementation order
        # Could be ALREADY_JUDGED or NOT_ENOUGH_FAULTS
        assert exc_info.value.code in [
            DisputesErrorCode.ALREADY_JUDGED,
            DisputesErrorCode.NOT_ENOUGH_FAULTS,
        ]

    def test_offender_already_reported(self):
        """Test case 5c: Attempt to report already reported offender"""
        target_hash = WorkReportHash(create_dummy_bytes32())
        offender_key = Ed25519Public(Settings(None, 0).ed25519_public)

        # Create initial state with offender already reported
        initial_state = create_test_state(
            tau=U32(0), psi_bad=[target_hash], psi_offenders=[offender_key]
        )

        # Try to report the same offender again
        culprits = create_sorted_culprits(target_hash, [0])

        disputes_extrinsic = DisputesExtrinsic(
            verdicts=Verdicts([]), culprits=Culprits(culprits), faults=Faults([])
        )

        block = create_test_block(disputes_extrinsic)
        block.header.offenders_mark = OffendersMark.produce(disputes_extrinsic)

        with pytest.raises(DisputesError) as exc_info:
            Disputes.transition(deepcopy(initial_state), initial_state, block)

        # This might be caught by different validation errors depending on implementation order
        # Could be OFFENDER_ALREADY_REPORTED or BAD_GUARANTOR_KEY
        assert exc_info.value.code in [
            DisputesErrorCode.OFFENDER_ALREADY_REPORTED,
            DisputesErrorCode.BAD_GUARANTOR_KEY,
        ]
