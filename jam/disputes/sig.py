import hashlib
from dataclasses import dataclass
import dataclasses
from typing import List, Set, Tuple
from math import floor
from ecdsa import VerifyingKey  # Hypothetical Ed25519 library; adjust as needed

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


@dataclass
class Disputes:
    @staticmethod
    def verify_signature(public_key: str, message: str, signature: str) -> bool:
        """
        Verify an Ed25519 signature against a public key and message.

        Args:
            public_key: Hex-encoded public key (e.g., ed25519 from kappa).
            message: Hex-encoded message being signed (e.g., target + vote).
            signature: Hex-encoded signature.

        Returns:
            bool: True if signature is valid, False otherwise.
        """
        try:
            vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve='ed25519')
            message_bytes = bytes.fromhex(message)
            signature_bytes = bytes.fromhex(signature)
            return vk.verify(signature_bytes, message_bytes)
        except Exception:
            return False
    @staticmethod
    def generate_fault_signature(private_key: str, vote: bool, target: str) -> str:
        """
        Generate an Ed25519 signature for a fault using a private key.

            Args:
            private_key: Hex-encoded private key (without '0x') for signing.
            vote: Boolean indicating the fault vote (True or False).
            target: Hex-encoded target hash (with '0x') to be signed.

        Returns:
            str: Hex-encoded signature (without '0x').
        """
        # a = bytes(private_key)
        # obj=Ed25519PrivateKey.from_private_bytes(a)
        # vote_byte = b'\x01' if vote else b'\x00'
            # byte_target = ByteUtils.bitarray_to_bytes(target[2:])  # Remove '0x' prefix and convert to bytes
            # message_bytes = vote_byte + byte_target
            # sign_bytes=obj.sign(message_bytes)
            # sign_hex=sign_bytes.hex()
            # print(sign_hex)
            
        try:
            # Convert private key from hex string to bytes
            private_key_bytes = bytes(private_key)
            private_key_obj = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            # Construct the message: vote (1 byte) + target (32 bytes)
            vote_byte = b'$jam_valid' if vote else b'$jam_invalid'
            target_bytes = ByteUtils.bitarray_to_bytes(target[2:])  # Remove '0x' prefix
            message_bytes = vote_byte + target_bytes

            # Generate the signature (64 bytes for Ed25519)
            signature_bytes = private_key_obj.sign(message_bytes)
            signature_hex = signature_bytes.hex()  # Convert to hex string
            return signature_hex
        except Exception as e:
            # raise ValueError(f"Failed to generate signature: {str(e)}")
            return None
        
    @staticmethod
    def transition(pre_state: State, block: Block) -> Tuple[State, dict]:
        """
        Transition the state with Disputes logic, enforcing verdict constraints and signature validation.

        Processes verdicts, culprits, and faults from the disputes extrinsic, updates the
        state's psi component, and ensures formal constraints:
        - Solely valid verdicts require at least one fault.
        - Solely invalid verdicts require at least two culprits.

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

        # Ensure psi sets are treated as sets, not lists
        new_state.psi.g = set(new_state.psi.g)
        new_state.psi.b = set(new_state.psi.b)
        new_state.psi.w = set(new_state.psi.w)
        new_state.psi.o = set(new_state.psi.o)

        # Verify verdicts are sorted by target (ascending order)
        for i in range(len(disputes.verdicts) - 1):
            if disputes.verdicts[i].target >= disputes.verdicts[i + 1].target:
                return new_state, {"err": "verdicts_not_sorted_unique"}

        # Signature validation for verdicts (before already_judged)
        for verdict in disputes.verdicts:
            seen_signatures = set()
            for vote in verdict.votes:
                validator_key = new_state.kappa[vote.index].ed25519
                message = str(verdict.target) + str(vote.vote).encode().hex()
                signature = vote.signature

                # Check for duplicate signatures
                if str(signature) in seen_signatures:
                    return new_state, {"err": "bad_signature"}
                seen_signatures.add(str(signature))

                # Verify signature
                if not Disputes.verify_signature(validator_key, message, signature):
                    return new_state, {"err": "bad_signature"}

        # Check if verdicts are already judged
        for verdict in disputes.verdicts:
            if str(verdict.target) in new_state.psi.g or str(verdict.target) in new_state.psi.b or str(verdict.target) in new_state.psi.w:
                return new_state, {"err": "already_judged"}

        # Verify culprits are sorted by key and match verdicts
        for i in range(len(disputes.culprits) - 1):
            if not any(str(disputes.culprits[i].target) == str(verdict.target) for verdict in disputes.verdicts):
                return new_state, {"err": "culprits_verdict_not_bad"}
            if disputes.culprits[i].key >= disputes.culprits[i + 1].key:
                return new_state, {"err": "culprits_not_sorted_unique"}

        # Verify faults are sorted by key (ascending order)
        for i in range(len(disputes.faults) - 1):
            if disputes.faults[i].key >= disputes.faults[i + 1].key:
                return new_state, {"err": "faults_not_sorted_unique"}

        # Process culprits with signature validation
        culprit_counts = {}
        for culprit in disputes.culprits:
            if str(culprit.key) in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            validator_key = next((v.ed25519 for v in new_state.kappa if v.ed25519 == culprit.key), None)
            if not validator_key:
                return new_state, {"err": "bad_signature"}
            message = str(culprit.target)
            if not Disputes.verify_signature(validator_key, message, culprit.signature):
                return new_state, {"err": "bad_signature"}
            new_state.psi.o.add(culprit.key)
            offenders_mark.add(culprit.key)
            culprit_counts[culprit.target] = culprit_counts.get(culprit.target, 0) + 1

        # Process faults
        fault_counts = {}
        for fault in disputes.faults:
            if str(fault.key) in new_state.psi.o:
                return new_state, {"err": "offender_already_reported"}
            validator_key = next((v.ed25519 for v in new_state.kappa if v.ed25519 == fault.key), None)
            if not validator_key:
                return new_state, {"err": "bad_signature"}
            message = str(fault.target) + str(fault.vote).encode().hex()
            if not Disputes.verify_signature(validator_key, message, fault.signature):
                return new_state, {"err": "bad_signature"}
            new_state.psi.o.add(fault.key)
            offenders_mark.add(fault.key)
            fault_counts[fault.target] = fault_counts.get(fault.target, 0) + 1

        # Process verdicts with constraints
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index (ascending order)
            for i in range(len(verdict.votes) - 1):
                if verdict.votes[i].index >= verdict.votes[i + 1].index:
                    return new_state, {"err": "judgements_not_sorted_unique"}

            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            total_votes = len(verdict.votes)

            # Solely valid verdict (all positive votes)
            if positive_votes == total_votes and total_votes >= VALIDATORS_SUPER_MAJORITY:
                if fault_counts.get(verdict.target, 0) < MINIMUM_FAULTS_FOR_GOOD:
                    return new_state, {"err": "not_enough_faults"}
                for fault in disputes.faults:
                    if fault.target == verdict.target and fault.vote:
                        return new_state, {"err": "fault_verdict_wrong"}
                if str(verdict.target) not in new_state.psi.g:
                    new_state.psi.g.add(str(verdict.target))

            # Solely invalid verdict (all negative votes)
            elif positive_votes == 0:
                if culprit_counts.get(verdict.target, 0) < MINIMUM_CULPRITS_FOR_BAD:
                    return new_state, {"err": "not_enough_culprits"}
                for fault in disputes.faults:
                    if fault.target == verdict.target and not fault.vote:
                        return new_state, {"err": "fault_verdict_wrong"}
                if str(verdict.target) not in new_state.psi.b:
                    new_state.psi.b.add(str(verdict.target))

            # Wonky verdict (mixed votes)
            elif positive_votes > 0 and positive_votes < VALIDATORS_SUPER_MAJORITY:
                if str(verdict.target) not in new_state.psi.w:
                    new_state.psi.w.add(str(verdict.target))
            else:
                return new_state, {"err": "bad_vote_split"}

        # Return success with offenders mark if any offenders were added
        if offenders_mark:
            return new_state, {"ok": {"offenders_mark": offenders_mark}}
        return new_state, {"ok": {"offenders_mark": []}}