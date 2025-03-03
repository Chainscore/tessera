from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum
from jam.utils.constants import RECENT_HISTORY_SIZE


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
    DUPLICATE_PACKAGE_IN_REPORT = "duplicate_package_in_report" # two same package exist in report
    DUPLICATE_PACKAGE_IN_RECENT_HISTORY = "dupliate_package_in_recent_history" # work package exist in recent block
    OUT_OF_ORDER_GUARANTEE = "out_of_order_guarantee" # core-index not in order
    TOO_MANY_DEPENDENCIES = "too_many_dependencies" # work package has may dependencies
