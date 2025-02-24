import hashlib
from dataclasses import dataclass
import dataclasses
from typing import List, Set, Tuple
from math import floor
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jam.types.base.sequences.bytes import ByteArray32, ByteArray64


from cryptography.exceptions import InvalidSignature

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
from jam.utils.byte_utils import ByteUtils
from jam.utils.constants import VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY, EPOCH_LENGTH

# Define minimum requirements
MINIMUM_FAULTS_FOR_GOOD = 1  # At least 1 fault for solely valid verdicts
MINIMUM_CULPRITS_FOR_BAD = 2  # At least 2 culprits for solely invalid verdicts
# MINIMUM_JUDGEMENT_AGE = 2  # Minimum age for a verdict to be valid

# TODO: Add a check for the age of the verdicts

@dataclass
class Disputes:
    
    @staticmethod
    def verify_signature(public_key: ByteArray32, message_bytes:bytes, target: bytes, signature: ByteArray64) -> bool:
        """
        Verify an Ed25519 signature using a public key.

        Args:
            public_key: ByteArray32 containing the Ed25519 public key (32 bytes).
            message_bytes: Bytes of the message that was signed.
            signature: ByteArray64 containing the Ed25519 signature (64 bytes).

        Returns:
            bool: True if the signature is valid, False otherwise.
        """
        
        # print("message_bytes---->",message,bytes(message))
        try:
            public_key_bytes = bytes(public_key)  # Convert ByteArray32 to bytes
            signature_bytes = bytes(signature)    # Convert ByteArray64 to bytes
            public_key_obj = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            # Convert vote to byte representation
            # vote_byte = b'jam_valid' if vote else b'jam_invalid'
            # message_bytes = bytes(vote_byte) + ByteUtils.bitarray_to_bytes(message[2:])
            msg_bytes = bytes(message_bytes) + bytes(target)
            public_key_obj.verify(signature_bytes, msg_bytes)
            print("Signature verified successfully")
            return True
        except InvalidSignature:
            print("InvalidSignature")
            return False
        except Exception as e:
            print(f"Signature verification failed: {e}")
        return False
    @staticmethod
    def transition(pre_state: State, block: Block) -> Tuple[State, dict]:
        """
        Transition the state with Disputes logic, enforcing verdict constraints.

        Processes verdicts, culprits, and faults from the disputes extrinsic, updates the
        state's psi component, and ensures formal constraints:
        - Solely valid verdicts require at least one fault.
        - Solely invalid verdicts require at least two culprits.
        # - Verdict age must be >= MINIMUM_JUDGEMENT_AGE.

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
        offenders_mark = set()  # Use set to ensure uniqueness
        # current_epoch = new_state.tau // EPOCH_LENGTH
        # valid_ages = [current_epoch, current_epoch - 1]
        # print("valid_ages",new_state.)
        # Ensure psi sets are treated as sets, not lists
        new_state.psi.g = set(new_state.psi.g)
        new_state.psi.b = set(new_state.psi.b)
        new_state.psi.w = set(new_state.psi.w)
        new_state.psi.o = set(new_state.psi.o)
        
        # Verify signatures for all faults
        for fault in disputes.faults:
            message_bytes = b'jam_valid' if fault.vote else b'jam_invalid'
            if not Disputes.verify_signature(fault.key, message_bytes, fault.target, fault.signature):
                return new_state, {"err": "bad_fault_signature"}
            else:
                print("Passed fault signature!!")
        
        # Verify signatures for all culprits
        for culprit in disputes.culprits:
            message_bytes = b'jam_guarantee'
            if not Disputes.verify_signature(culprit.key, message_bytes, culprit.target, culprit.signature):
                return new_state, {"err": "bad_culprit_signature"}
            else:
                print("Passed culprit signature!!")
        
        # Verify signatures for all votes in each verdict
        for verdict in disputes.verdicts:
            for vote in verdict.votes:
                # Get the public key from the validator key-set
                validator = pre_state.kappa[vote.index]
                public_key = validator.ed25519

                # Get the vote value and message
                message_bytes = b'jam_valid' if vote.vote else b'jam_invalid'
                message = verdict.target
                signature = vote.signature

                # Verify the signature
                if not Disputes.verify_signature(public_key, message_bytes, verdict.target, signature):
                    print(f"Signature verification failed for vote index {vote.index}")
                    return new_state, {"err": "bad_vote_signature"}
                else:
                    print(f"Signature verified for vote index {vote.index}")
        # Verify verdicts are sorted by target (ascending order)
        for i in range(len(disputes.verdicts) - 1):
            if disputes.verdicts[i].target >= disputes.verdicts[i + 1].target:
                return new_state, {"err": "verdicts_not_sorted_unique"}
        
        # Check if verdicts are already judged and validate age
        for verdict in disputes.verdicts:
            if str(verdict.target) in new_state.psi.g or str(verdict.target) in new_state.psi.b or str(verdict.target) in new_state.psi.w:
                return new_state, {"err": "already_judged"}
            # if verdict.age > new_state.tau:  # Dispute from future
            #     return new_state, {"err": "invalid_age"}
            # if verdict.age < MINIMUM_JUDGEMENT_AGE:  # Too recent
            #     return new_state, {"err": "bad_judgement_age"}
        
        # Verify culprits are sorted by key (ascending order)
        for i in range(len(disputes.culprits) - 1):
            if not any(str(disputes.culprits[i].target) == str(verdict.target) for verdict in disputes.verdicts):
                return new_state, {"err": "culprits_verdict_not_bad"}
            if disputes.culprits[i].key >= disputes.culprits[i + 1].key:
                return new_state, {"err": "culprits_not_sorted_unique"}

        # Verify faults are sorted by key (ascending order)
        for i in range(len(disputes.faults) - 1):
            if disputes.faults[i].key >= disputes.faults[i + 1].key:
                return new_state, {"err": "faults_not_sorted_unique"}

        # Process culprits and check for offenders already reported
        culprit_counts = {}  # Track culprits per target
        for culprit in disputes.culprits:
            if str(culprit.key) in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            new_state.psi.o.add(culprit.key)
            offenders_mark.add(culprit.key)
            culprit_counts[culprit.target] = culprit_counts.get(culprit.target, 0) + 1

        # Process faults and check for offenders already reported
        fault_counts = {}  # Track faults per target
        for fault in disputes.faults:
            if str(fault.key) in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            new_state.psi.o.add(fault.key)
            offenders_mark.add(fault.key)
            fault_counts[fault.target] = fault_counts.get(fault.target, 0) + 1

        # Process verdicts with constraints
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index (ascending order)
            for i in range(len(verdict.votes) - 1):
                if verdict.votes[i].index >= verdict.votes[i + 1].index:
                    return new_state, {"err": "judgements_not_sorted_unique"}
            # Check if dispute is too old
            # if disputes.verdicts[0].age > (new_state.tau//(EPOCH_LENGTH*100)) :
            #     return new_state, {"err": "dispute_too_old"}
            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            total_votes = len(verdict.votes)

            # Solely valid verdict (all positive votes)
            if positive_votes == total_votes and total_votes >= VALIDATORS_SUPER_MAJORITY:
                # Check for at least one fault (constraint: solely valid implies ≥1 fault)
                if fault_counts.get(verdict.target, 0) < MINIMUM_FAULTS_FOR_GOOD:
                    return new_state, {"err": "not_enough_faults"}
                # Check fault_verdict_wrong (faults must contradict the verdict)
                for fault in disputes.faults:
                    if fault.target == verdict.target and fault.vote:
                        return new_state, {"err": "fault_verdict_wrong"}
                if verdict.target not in new_state.psi.g:
                    new_state.psi.g.add(verdict.target)

            # Solely invalid verdict (all negative votes)
            elif positive_votes == 0:
                # Check for at least two culprits (constraint: solely invalid implies ≥2 culprits)
                if culprit_counts.get(verdict.target, 0) < MINIMUM_CULPRITS_FOR_BAD:
                    return new_state, {"err": "not_enough_culprits"}
                # Check fault_verdict_wrong (faults must not contradict a bad verdict)
                for fault in disputes.faults:
                    if fault.target == verdict.target and not fault.vote:
                        return new_state, {"err": "fault_verdict_wrong"}
                if verdict.target not in new_state.psi.b:
                    new_state.psi.b.add(verdict.target)

            # Wonky verdict (mixed votes meeting wonky threshold)
            elif positive_votes > 0 and positive_votes < VALIDATORS_SUPER_MAJORITY:
                if verdict.target not in new_state.psi.w:
                    new_state.psi.w.add(verdict.target)
            else:
                return new_state, {"err": "bad_vote_split"}

        # Return success with sorted offenders mark if any offenders were added
        if offenders_mark:
            return new_state, {"ok": {"offenders_mark": offenders_mark}}
        return new_state, {"ok": {"offenders_mark": []}}