import hashlib
from dataclasses import dataclass
import dataclasses
from typing import List, Set, Tuple
from math import floor

from jam.types.block import Block
from jam.state.state import State
from jam.types.extrinsics.disputes import (
    DisputesExtrinsic,
    Verdict,
    Culprit,
    Fault,
    DisputesRecords,
)
from jam.state.components.psi import Psi, PsiG, PsiB, PsiW, PsiO
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY

# Define minimum requirements
MINIMUM_FAULTS_FOR_GOOD = 1  # At least 1 fault for solely valid verdicts
MINIMUM_CULPRITS_FOR_BAD = 2  # At least 2 culprits for solely invalid verdicts
MINIMUM_JUDGEMENT_AGE = 2  # Minimum age for a verdict to be valid


@dataclass
class Disputes:
    @staticmethod
    def transition(pre_state: State, block: Block) -> Tuple[State, dict]:
        """
        Transition the state with Disputes logic, enforcing verdict constraints.

        Processes verdicts, culprits, and faults from the disputes extrinsic, updates the
        state's psi component, and ensures formal constraints:
        - Solely valid verdicts require at least one fault.
        - Solely invalid verdicts require at least two culprits.
        - Verdict age must be >= MINIMUM_JUDGEMENT_AGE.

        Args:
            pre_state: State before transition
            block: Block containing disputes extrinsic
            
        Returns:
            Tuple containing:
            - Updated state after processing disputes
            - Output dictionary with 'ok' or 'err' status and details
        """
        new_state = dataclasses.replace(pre_state)
        disputes = block.extrinsic.disputes
        output = {"err": None, "ok": None}
        offenders_mark = set()

        # Ensure psi sets are treated as sets
        new_state.psi.g = set(new_state.psi.g)
        new_state.psi.b = set(new_state.psi.b)
        new_state.psi.w = set(new_state.psi.w)
        new_state.psi.o = set(new_state.psi.o)

        # Verify verdicts are sorted by target (ascending order)
        for i in range(len(disputes.verdicts) - 1):
            if disputes.verdicts[i].target >= disputes.verdicts[i + 1].target:
                return new_state, {"err": "verdicts_not_sorted_unique"}

        # Check if verdicts are already judged and validate age
        for verdict in disputes.verdicts:
            if verdict.target in new_state.psi.g or verdict.target in new_state.psi.b or verdict.target in new_state.psi.w:
                return new_state, {"err": "already_judged"}
            if verdict.age > new_state.tau:  # Dispute from future
                return new_state, {"err": "invalid_age"}
            if verdict.age < MINIMUM_JUDGEMENT_AGE:  # Too recent
                return new_state, {"err": "bad_judgement_age"}

        # Process verdicts first to determine bad targets
        bad_verdict_targets = set()
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index (ascending order)
            for i in range(len(verdict.votes) - 1):
                if verdict.votes[i].index >= verdict.votes[i + 1].index:
                    return new_state, {"err": "judgements_not_sorted_unique"}

            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            total_votes = len(verdict.votes)

            if positive_votes == total_votes and total_votes >= VALIDATORS_SUPER_MAJORITY:
                if fault_counts.get(verdict.target, 0) < MINIMUM_FAULTS_FOR_GOOD:
                    return new_state, {"err": "not_enough_faults"}
                for fault in disputes.faults:
                    if fault.target == verdict.target and fault.vote:
                        return new_state, {"err": "fault_verdict_wrong"}
                if verdict.target not in new_state.psi.g:
                    new_state.psi.g.add(verdict.target)
            elif positive_votes == 0:
                bad_verdict_targets.add(verdict.target)
            elif positive_votes > 0 and positive_votes < VALIDATORS_SUPER_MAJORITY:
                if verdict.target not in new_state.psi.w:
                    new_state.psi.w.add(verdict.target)
            else:
                return new_state, {"err": "bad_vote_split"}

        # Verify culprits are sorted by key and match bad verdicts
        for i in range(len(disputes.culprits) - 1):
            if disputes.culprits[i].target not in bad_verdict_targets:
                return new_state, {"err": "culprits_verdict_not_bad"}
            if disputes.culprits[i].key >= disputes.culprits[i + 1].key:
                return new_state, {"err": "culprits_not_sorted_unique"}

        # Process culprits and check for offenders already reported
        culprit_counts = {}
        for culprit in disputes.culprits:
            if culprit.key in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            new_state.psi.o.add(culprit.key)
            offenders_mark.add(culprit.key)
            culprit_counts[culprit.target] = culprit_counts.get(culprit.target, 0) + 1

        # Verify faults are sorted by key (ascending order)
        for i in range(len(disputs.faults) - 1):
            if disputes.faults[i].key >= disputes.faults[i + 1].key:
                return new_state, {"err": "faults_not_sorted_unique"}

        # Process faults and check for offenders already reported
        fault_counts = {}
        for fault in disputes.faults:
            if fault.key in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            new_state.psi.o.add(fault.key)
            offenders_mark.add(fault.key)
            fault_counts[fault.target] = fault_counts.get(fault.target, 0) + 1

        # Finalize bad verdicts after culprit counts are confirmed
        for target in bad_verdict_targets:
            if culprit_counts.get(target, 0) < MINIMUM_CULPRITS_FOR_BAD:
                return new_state, {"err": "not_enough_culprits"}
            for fault in disputes.faults:
                if fault.target == target and not fault.vote:
                    return new_state, {"err": "fault_verdict_wrong"}
            if target not in new_state.psi.b:
                new_state.psi.b.add(target)

        # Return success with offenders mark if any offenders were added
        if offenders_mark:
            return new_state, {"ok": {"offenders_mark": offenders_mark}}
        return new_state, {"ok": {"offenders_mark": []}}