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
    DisputesRecords
)
from jam.state.components.psi import Psi, PsiG, PsiB, PsiW, PsiO
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY


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
        for i in range(len(disputes.verdicts)-1):
            if disputes.verdicts[i].target >= disputes.verdicts[i+1].target:
                return new_state, {"err": "verdicts_not_sorted_unique"}
        
        # Verify culprits are sorted by key
        for i in range(len(disputes.culprits)-1):
            if disputes.culprits[i].key >= disputes.culprits[i+1].key:
                return new_state, {"err": "culprits_not_sorted_unique"}
        # Verify faults are sorted by key
        for i in range(len(disputes.faults)-1):
            if disputes.faults[i].key >= disputes.faults[i+1].key:
                return new_state, {"err": "faults_not_sorted_unique"}
        
        

        for culprit in disputes.culprits:
            if culprit.key not in new_state.psi.o:
                new_state.psi.o.append(culprit.key)
                offenders_mark.append(culprit.key)
            
        # Process faults    
        for fault in disputes.faults:
            if fault.key not in new_state.psi.o:
                new_state.psi.o.append(fault.key)
                offenders_mark.append(fault.key)
        
        
        # Process verdicts
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index
            # Check if votes are sorted by index

            for i in range(len(verdict.votes)-1):
                if verdict.votes[i].index >= verdict.votes[i+1].index:
                    return new_state, {"err": "judgements_not_sorted_unique"}

            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            
            # Check if verdict meets supermajority threshold
            if positive_votes == VALIDATORS_SUPER_MAJORITY:
                # Add to good set if not already present
                if verdict.target not in new_state.psi.g:
                    new_state.psi.g.append(verdict.target)
                    
            elif positive_votes == 0:
                # Add to bad set if not already present
                if verdict.target not in new_state.psi.b:
                    new_state.psi.b.append(verdict.target)
            elif positive_votes == VALIDATORS_WONKY:
                # Add to wonky set if not already present
                if verdict.target not in new_state.psi.w:
                    new_state.psi.w.append(verdict.target)
            else:
                # return error if vote split is not valid
                return new_state, {"err": "bad_vote_split"}

        # Clear any work reports that were judged as bad or wonky
        # for core in range(len(new_state.rho)):
        #     work_report = new_state.rho[core]
        #     if work_report and work_report.hash in (set(new_state.psi.b) | set(new_state.psi.w)):
        #         new_state.rho[core] = None

        # Return success with sorted offenders mark if any offenders were added
        if offenders_mark:
            return new_state, {"ok": {"offenders_mark": offenders_mark}}
        return new_state, {"ok": {"offenders_mark": []}}