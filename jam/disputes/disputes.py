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
    DisputesRecords
)
from jam.state.components.psi import Psi, PsiG, PsiB, PsiW, PsiO
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY


class Disputes:
    @staticmethod
    def transition(pre_state: State, block: Block) -> Tuple[State, dict]:
        """
        Transition the state with Disputes logic.
        
        This method processes verdicts, culprits, and faults from the disputes extrinsic,
        updating the state's psi component and clearing invalid work reports from cores.
        
        Args:
            pre_state: State before transition
            block: Block containing disputes extrinsic
            
        Returns:
            Tuple containing:
            - Updated state after processing disputes
            - Output dictionary with 'ok' or 'err' status and details
        """
        # Make a copy of the state
        new_state = dataclasses.replace(pre_state)
        disputes = block.extrinsic.disputes
        output = {"err": None, "ok": None}
        offenders_mark = []

        # Verify verdicts are sorted by target
        sorted_verdicts = sorted(disputes.verdicts, key=lambda v: v.target)
        if sorted_verdicts != disputes.verdicts:
            return new_state, {"err": "verdicts_not_sorted_unique"}

        # Process verdicts
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index
            sorted_votes = sorted(verdict.votes, key=lambda v: v.index)
            if sorted_votes != verdict.votes:
                return new_state, {"err": "judgements_not_sorted_unique"}

            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            
            # Check if verdict meets supermajority threshold
            if positive_votes == VALIDATORS_SUPER_MAJORITY:
                # Add to good set if not already present
                if verdict.target not in new_state.psi.g:
                    new_state.psi.g.add(verdict.target)
                    
            elif positive_votes == 0:
                # Add to bad set if not already present
                if verdict.target not in new_state.psi.b:
                    new_state.psi.b.add(verdict.target)
            else:
                # Add to wonky set if not already present
                if verdict.target not in new_state.psi.w:
                    new_state.psi.w.add(verdict.target)

        # Process culprits and faults
        # Verify culprits are sorted by key
        sorted_culprits = sorted(disputes.culprits, key=lambda c: c.key)
        if sorted_culprits != disputes.culprits:
            return new_state, {"err": "culprits_not_sorted_unique"}

        # Process culprits
        for culprit in disputes.culprits:
            if culprit.key not in new_state.psi.o:
                new_state.psi.o.add(culprit.key)
                offenders_mark.append(culprit.key)
            
        # Verify faults are sorted by key
        sorted_faults = sorted(disputes.faults, key=lambda f: f.key)
        if sorted_faults != disputes.faults:
            return new_state, {"err": "faults_not_sorted_unique"}

        # Process faults    
        for fault in disputes.faults:
            if fault.key not in new_state.psi.o:
                new_state.psi.o.add(fault.key)
                offenders_mark.append(fault.key)

        # Clear any work reports that were judged as bad or wonky
        for core in range(len(new_state.rho)):
            work_report = new_state.rho[core]
            if work_report and work_report.hash in (set(new_state.psi.b) | set(new_state.psi.w)):
                new_state.rho[core] = None

        # Return success with sorted offenders mark if any offenders were added
        if offenders_mark:
            return new_state, {"ok": {"offenders_mark": sorted(offenders_mark)}}
        return new_state, {"ok": {"offenders_mark": []}}