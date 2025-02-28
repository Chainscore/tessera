from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum


class ReportingError(JamError):
    ...

@decodable_enum
class ReportingErrorCode(Enum):
    """Error codes for the Reporting STF protocol."""

    NOT_AUTHERIZED = "not_autherized"  # Work package not executed
    BAD_VALIDATOR_INDEX = "bad_validator_index"  # validator index is not valid
    NOT_ENOUGH_GUARANTEE = "not_enough_guarantee"  # Work report don't have enough validator
    NOT_SORTED_GUARANTOR = "not_sorted_guarantor"  # work Report's guarantee Validators are not sorted
    BAD_CORE_INDEX = "bad_ore_index" # core index in not exist

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
