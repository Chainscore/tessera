from tsrkit_types.enum import Enum
from jam.error import JamError

class DisputesError(JamError):
    ...

class DisputesErrorCode(Enum):
    """Error codes for the Disputes STF protocol."""

    BAD_SIGNATURE = "bad_signature"  # Invalid signature
    BAD_JUDGEMENT_AGE = "bad_judgement_age"  # Judgement age is not valid
    VERDICTS_NOT_SORTED_UNIQUE = "verdicts_not_sorted_unique"  # Verdicts not sorted in ascending order
    CULPRITS_NOT_SORTED_UNIQUE = "culprits_not_sorted_unique"  # Culprits not sorted in ascending order
    FAULTS_NOT_SORTED_UNIQUE = "faults_not_sorted_unique"  # Faults not sorted in ascending order
    CULPRITS_VERDICT_NOT_BAD = "culprits_verdict_not_bad"  # Culprits verdict is not bad
    FAULTS_VERDICT_NOT_BAD = "faults_verdict_not_bad"  # Faults verdict is not bad
    ALREADY_JUDGED = "already_judged"  # Already judged
    JUDGEMENTS_NOT_SORTED_UNIQUE = "judgements_not_sorted_unique"  # Judgements not sorted in ascending order
    OFFENDER_ALREADY_REPORTED = "offender_already_reported"  # Offender already reported
    NOT_ENOUGH_FAULTS = "not_enough_faults"  # Not enough faults
    NOT_ENOUGH_CULPRITS = "not_enough_culprits"  # Not enough culprits
    FAULT_VERDICT_WRONG = "fault_verdict_wrong"  # Fault verdict is wrong
    BAD_VOTE_SPLIT = "bad_vote_split"  # Bad vote split
    BAD_GUARANTOR_KEY = "bad_guarantor_key"
    BAD_AUDITOR_KEY= "bad_auditor_key"
