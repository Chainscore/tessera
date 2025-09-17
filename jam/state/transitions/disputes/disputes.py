from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tsrkit_types.bytes import Bytes
from tsrkit_types.null import Null

from jam.state.transitions.disputes.error import DisputesError, DisputesErrorCode
from jam.types import PsiG, PsiB, PsiW, PsiO, Psi
from jam.types.state.rho import OptionalWorkReportState
from jam.types.state.sigma import Sigma
from jam.block import Block, OffendersMark, DisputesExtrinsic
from jam.types.protocol.crypto import Hash
from jam.utils.constants import EPOCH_LENGTH, VALIDATORS_SUPER_MAJORITY, VALIDATORS_WONKY, X

# Define minimum requirements
MINIMUM_FAULTS_FOR_GOOD = 1  # At least 1 fault for solely valid verdicts
MINIMUM_CULPRITS_FOR_BAD = 2  # At least 2 culprits for solely invalid verdicts


class Disputes:

    @staticmethod
    def transition(pre_state: Sigma, state: Sigma, block: Block) -> Sigma:
        # 1. Disputes Transition

        # Get Disputes Extrinsic format
        disputes = block.extrinsic.disputes

        # epoch Index
        current_epoch = pre_state.tau // EPOCH_LENGTH
        pre_psi = pre_state.psi
        pre_lambda = pre_state.lambda_
        pre_kappa = pre_state.kappa

        # 2. Valid age
        valid_ages = (
            [current_epoch, current_epoch]
            if current_epoch == 0
            else [current_epoch, current_epoch - 1]
        )

        # 3. Pre States
        good_set = set(pre_psi.good)
        bad_set = set(pre_psi.bad)
        wonky_set = set(pre_psi.wonky)
        offenders_set = set(pre_psi.offenders)

        rho_dagger = pre_state.rho

        val_keys = {v.ed25519 for v in pre_lambda} | {v.ed25519 for v in pre_kappa}

        # 4. Verifying signatures
        # Verifying fault signatures
        for fault in disputes.faults:
            try:
                message_bytes = (X.VALID if fault.vote else X.INVALID).value
                Ed25519PublicKey.from_public_bytes(fault.key).verify(
                    fault.signature, message_bytes + fault.target
                )
            except InvalidSignature:
                raise DisputesError(DisputesErrorCode.BAD_SIGNATURE)
            if fault.key not in val_keys:
                raise DisputesError(DisputesErrorCode.BAD_AUDITOR_KEY)

        # Verifying culprit signatures
        for culprit in disputes.culprits:
            try:
                message_bytes = X.GUARANTEE.value
                Ed25519PublicKey.from_public_bytes(culprit.key).verify(
                    culprit.signature, message_bytes + culprit.target
                )
            except InvalidSignature:
                raise DisputesError(DisputesErrorCode.BAD_SIGNATURE)
            if culprit.key not in val_keys:
                raise DisputesError(DisputesErrorCode.BAD_GUARANTOR_KEY)

        # Verifying verdicts are sorted by target
        for verdict in disputes.verdicts:
            if verdict.age not in valid_ages:
                raise DisputesError(DisputesErrorCode.BAD_JUDGEMENT_AGE)
            for vote in verdict.votes:
                # Get the public key from the validator key-set
                if verdict.age == valid_ages[0]:
                    validator = pre_kappa[vote.index]
                    public_key = validator.ed25519
                else:
                    validator = pre_lambda[vote.index]
                    public_key = validator.ed25519

                # Get the vote value and message
                try:
                    message_bytes = (X.VALID if vote.vote else X.INVALID).value
                    Ed25519PublicKey.from_public_bytes(public_key).verify(
                        vote.signature, message_bytes + verdict.target
                    )
                except InvalidSignature:
                    raise DisputesError(DisputesErrorCode.BAD_SIGNATURE)

        # 5. Validate verdicts
        # Verify verdicts are sorted by target (ascending order)
        for i in range(len(disputes.verdicts) - 1):
            if disputes.verdicts[i].target >= disputes.verdicts[i + 1].target:
                raise DisputesError(DisputesErrorCode.VERDICTS_NOT_SORTED_UNIQUE)

        # Check if verdicts are already judged and validate age
        for verdict in disputes.verdicts:
            if (
                verdict.target in pre_state.psi.good
                or verdict.target in pre_state.psi.bad
                or verdict.target in pre_state.psi.wonky
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
            if culprit.key in pre_state.psi.offenders:
                raise DisputesError(DisputesErrorCode.OFFENDER_ALREADY_REPORTED)
            if culprit.key not in offenders_set:
                offenders_set.add(culprit.key)
            culprit_counts[culprit.target] = culprit_counts.get(culprit.target, 0) + 1

        # Process faults and check for offenders already reported
        fault_counts = {}  # Track faults per target
        for fault in disputes.faults:
            if fault.key in pre_state.psi.offenders:
                raise DisputesError(DisputesErrorCode.OFFENDER_ALREADY_REPORTED)
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
            if positive_votes == total_votes and total_votes >= VALIDATORS_SUPER_MAJORITY:
                # Check for at least one fault (constraint: solely valid implies ≥1 fault)
                if fault_counts.get(verdict.target, 0) < MINIMUM_FAULTS_FOR_GOOD:
                    raise DisputesError(DisputesErrorCode.NOT_ENOUGH_FAULTS)
                # Check fault_verdict_wrong (faults must contradict the verdict)
                for fault in disputes.faults:
                    if fault.target == verdict.target and fault.vote:
                        raise DisputesError(DisputesErrorCode.FAULT_VERDICT_WRONG)
                if verdict.target not in pre_state.psi.good:
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
                if verdict.target not in pre_state.psi.bad:
                    bad_set.add(verdict.target)

            # Wonky verdict (mixed votes meeting wonky threshold)
            elif positive_votes == VALIDATORS_WONKY:  # Condition for wonky verdict EXACTLY
                if verdict.target not in pre_state.psi.wonky:
                    wonky_set.add(verdict.target)
            else:
                raise DisputesError(DisputesErrorCode.BAD_VOTE_SPLIT)

        for i in range(len(pre_state.rho)):
            rep = pre_state.rho[i].unwrap()
            if rep != Null:
                try:
                    target = rep.report.hash()
                    if target in bad_set:
                        rho_dagger[i] = OptionalWorkReportState(Null)
                    if target in wonky_set:
                        rho_dagger[i] = OptionalWorkReportState(Null)
                except Exception:
                    pass

        # 9. Update of the Disputes states and return the new state
        # Update of the Disputes states
        offenders_set = sorted(offenders_set)

        state.psi = Psi(PsiG(list(good_set)), PsiB(list(bad_set)), PsiW(list(wonky_set)), PsiO(offenders_set))
        state.rho = rho_dagger

        return state
