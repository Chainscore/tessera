from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tsrkit_types.bytes import Bytes
from tsrkit_types.null import Null

from jam.disputes.error import DisputesError, DisputesErrorCode
from jam.types.state.rho import OptionalWorkReportState
from jam.types.state.sigma import Sigma
from jam.types.block import Block, OffendersMark, DisputesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.utils.constants import (
    EPOCH_LENGTH,
    VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY
)

# Define minimum requirements
MINIMUM_FAULTS_FOR_GOOD = 1  # At least 1 fault for solely valid verdicts
MINIMUM_CULPRITS_FOR_BAD = 2  # At least 2 culprits for solely invalid verdicts


@dataclass
class Disputes:
    @staticmethod
    def verify_signature(
        public_key: Bytes[32],
        message_bytes: bytes,
        target: bytes,
        signature: Bytes[64],
    ) -> bool:
        """
        Verify an Ed25519 signature using a public key.

        Args:
            public_key: ByteArray32 containing the Ed25519 public key (32 bytes).
            message_bytes: Bytes of the message that was signed.
            signature: ByteArray64 containing the Ed25519 signature (64 bytes).
            target: Bytes of the target that was signed.
        Returns:
            bool: True if the signature is valid, False otherwise.
        """

        try:
            public_key_bytes = bytes(public_key)  # Convert ByteArray32 to bytes
            signature_bytes = bytes(signature)  # Convert ByteArray64 to bytes
            public_key_obj = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            msg_bytes = bytes(message_bytes) + bytes(target)
            public_key_obj.verify(signature_bytes, msg_bytes)
            return True
        except InvalidSignature:
            return False
        except Exception as e:
            print(f"Signature verification failed: {e}")
        return False

    @staticmethod
    def transition(state: Sigma, block: Block) -> Sigma:
        # 1. Disputes Transition

        # Get Disputes Extrinsic format
        disputes = block.extrinsic.disputes

        # epoch Index
        current_epoch = state.tau // EPOCH_LENGTH

        # 2. Valid age
        valid_ages = (
            [current_epoch, current_epoch]
            if current_epoch == 0
            else [current_epoch, current_epoch - 1]
        )

        # 3. Psi sets
        good_set = set()
        bad_set = set()
        wonky_set = set()
        offenders_set = set()

        # 4. Verifying signatures
        # Verifying fault signatures
        for fault in disputes.faults:
            message_bytes = b"jam_valid" if fault.vote else b"jam_invalid"
            if not Disputes.verify_signature(
                fault.key, message_bytes, fault.target, fault.signature
            ):
                raise DisputesError(DisputesErrorCode.BAD_SIGNATURE)
            if fault.key not in [v.ed25519
                for v in (*state.lambda_, *state.kappa)]:
                raise DisputesError(DisputesErrorCode.BAD_AUDITOR_KEY)


        # Verifying culprit signatures
        for culprit in disputes.culprits:
            message_bytes = b"jam_guarantee"
            if not Disputes.verify_signature(
                culprit.key, message_bytes, culprit.target, culprit.signature
            ):
                raise DisputesError(DisputesErrorCode.BAD_SIGNATURE)
            if culprit.key not in [validator.ed25519
                for validator in (*state.lambda_, *state.kappa)]:
                raise DisputesError(DisputesErrorCode.BAD_GUARANTOR_KEY)


        # Verifying verdicts are sorted by target
        for verdict in disputes.verdicts:
            if verdict.age not in valid_ages:
                raise DisputesError(DisputesErrorCode.BAD_JUDGEMENT_AGE)
            for vote in verdict.votes:
                # Get the public key from the validator key-set
                if verdict.age == valid_ages[0]:
                    validator = state.kappa[vote.index]
                    public_key = validator.ed25519
                else:
                    validator = state.lambda_[vote.index]
                    public_key = validator.ed25519

                # Get the vote value and message
                message_bytes = b"jam_valid" if vote.vote else b"jam_invalid"
                message = verdict.target
                signature = vote.signature

                # Verify the vote signature
                if not Disputes.verify_signature(
                    public_key, message_bytes, verdict.target, signature
                ):
                    raise DisputesError(
                        DisputesErrorCode.BAD_SIGNATURE,
                    )

        # 5. Validate verdicts
        # Verify verdicts are sorted by target (ascending order)
        for i in range(len(disputes.verdicts) - 1):
            if disputes.verdicts[i].target >= disputes.verdicts[i + 1].target:
                raise DisputesError(DisputesErrorCode.VERDICTS_NOT_SORTED_UNIQUE)

        # Check if verdicts are already judged and validate age
        for verdict in disputes.verdicts:
            if (
                verdict.target in state.psi.good
                or verdict.target in state.psi.bad
                or verdict.target in state.psi.wonky
            ):
                raise DisputesError(DisputesErrorCode.ALREADY_JUDGED)

        # Verify culprits are sorted by key (ascending order)
        for i in range(len(disputes.culprits) - 1):
            if not any(
                str(disputes.culprits[i].target) == str(verdict.target)
                for verdict in disputes.verdicts
            ):
                raise DisputesError(DisputesErrorCode.CULPRITS_VERDICT_NOT_BAD)
            if disputes.culprits[i].key >= disputes.culprits[i + 1].key:
                raise DisputesError(DisputesErrorCode.CULPRITS_NOT_SORTED_UNIQUE)

        # 6. Validate faults and culprits
        # Verify faults are sorted by key (ascending order)
        for i in range(len(disputes.faults) - 1):
            if disputes.faults[i].key >= disputes.faults[i + 1].key:
                raise DisputesError(DisputesErrorCode.FAULTS_NOT_SORTED_UNIQUE)

        # Process culprits and check for offenders already reported
        culprit_counts = {}  # Track culprits per target
        for culprit in disputes.culprits:
            if culprit.key in state.psi.offenders:
                raise DisputesError(DisputesErrorCode.OFFENDER_ALREADY_REPORTED)
            # new_state.psi.offenders.append(culprit.key)
            if culprit.key not in offenders_set:
                offenders_set.add(culprit.key)
            culprit_counts[culprit.target] = culprit_counts.get(culprit.target, 0) + 1

        # Process faults and check for offenders already reported
        fault_counts = {}  # Track faults per target
        for fault in disputes.faults:
            if fault.key in state.psi.offenders:
                raise DisputesError(DisputesErrorCode.OFFENDER_ALREADY_REPORTED)
            # new_state.psi.offenders.append(fault.key)
            if fault.key not in offenders_set:
                offenders_set.add(fault.key)
            fault_counts[fault.target] = fault_counts.get(fault.target, 0) + 1

        # 7. Process verdicts with constraints
        # Process verdicts with constraints
        for verdict in disputes.verdicts:
            # Verify votes are sorted by validator index (ascending order)
            for i in range(len(verdict.votes) - 1):
                if verdict.votes[i].index >= verdict.votes[i + 1].index:
                    raise DisputesError(DisputesErrorCode.JUDGEMENTS_NOT_SORTED_UNIQUE)

            positive_votes = sum(1 for judgment in verdict.votes if judgment.vote)
            total_votes = len(verdict.votes)

            # Solely valid verdict (all positive votes)
            if (
                positive_votes == total_votes
                and total_votes >= VALIDATORS_SUPER_MAJORITY
            ):
                # Check for at least one fault (constraint: solely valid implies ≥1 fault)
                if fault_counts.get(verdict.target, 0) < MINIMUM_FAULTS_FOR_GOOD:
                    raise DisputesError(DisputesErrorCode.NOT_ENOUGH_FAULTS)
                # Check fault_verdict_wrong (faults must contradict the verdict)
                for fault in disputes.faults:
                    if fault.target == verdict.target and fault.vote:
                        raise DisputesError(DisputesErrorCode.FAULT_VERDICT_WRONG)
                if verdict.target not in state.psi.good:
                    good_set.add(verdict.target)

            # Solely invalid verdict (all negative votes)
            elif positive_votes == 0:
                # Check for at least two culprits (constraint: solely invalid implies ≥2 culprits)
                if culprit_counts.get(verdict.target, 0) < MINIMUM_CULPRITS_FOR_BAD:
                    raise DisputesError(DisputesErrorCode.NOT_ENOUGH_CULPRITS)
                # Check fault_verdict_wrong (faults must not contradict a bad verdict)
                for fault in disputes.faults:
                    if fault.target == verdict.target and not fault.vote:
                        raise DisputesError(DisputesErrorCode.FAULT_VERDICT_WRONG)
                if verdict.target not in state.psi.bad:
                    bad_set.add(verdict.target)

            # Wonky verdict (mixed votes meeting wonky threshold)
            elif (
                positive_votes == VALIDATORS_WONKY
            ):  # Condition for wonky verdict EXACTLY
                if verdict.target not in state.psi.wonky:
                    wonky_set.add(verdict.target)
            else:
                raise DisputesError(DisputesErrorCode.BAD_VOTE_SPLIT)

        # 8. Remove wrong targets from the rho array
        # TODO: Change the rho array when the new types are implemented.
        # Removing the wrong targets from the rho array
        for i in range(len(state.rho)):
            if state.rho[i] != Null:
                try:
                    target = Hash.blake2b(state.rho[i].get_value().report.encode())
                    if target in bad_set:
                        state.rho[i] = OptionalWorkReportState(Null)
                    if target in wonky_set:
                        state.rho[i] = OptionalWorkReportState(Null)
                except Exception:
                    pass

        # 9. Update of the Disputes states and return the new state
        # Update of the Disputes states
        offenders_set = sorted(offenders_set)
        for i in good_set:
            if i not in state.psi.good:
                state.psi.good.append(i)
        for i in bad_set:
            if i not in state.psi.bad:
                state.psi.bad.append(i)
        for i in wonky_set:
            if i not in state.psi.wonky:
                state.psi.wonky.append(i)
        for i in offenders_set:
            if i not in state.psi.offenders:
                state.psi.offenders.append(i)
        return state

    @staticmethod
    def get_offenders_mark(disputes: DisputesExtrinsic) -> OffendersMark:
        """
        Returns the offenders mark for all new disputes reported. Get all the keys of culprits and faults
        and return the offenders mark.
        https://graypaper.fluffylabs.dev/#/68eaa1f/131c00131c00?v=0.6.4
        """
        c_keys = [culprit.key for culprit in disputes.culprits]
        f_keys = [fault.key for fault in disputes.faults]
        offenders = list(set(c_keys + f_keys))
        return OffendersMark(offenders)
