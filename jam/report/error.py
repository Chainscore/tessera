from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum
from jam.utils.constants import RECENT_HISTORY_SIZE


class ReportingError(JamError):
    ...

@decodable_enum
class ReportingErrorCode(Enum):
    """Error codes for the Reporting STF protocol."""

    CORE_UNAUTHORIZED = "core_unauthorized"  # Work package not executed
    BAD_VALIDATOR_INDEX = "bad_validator_index"  # validator index is not valid
    NOT_ENOUGH_GUARANTEE = "not_enough_guarantee"  # Work report don't have enough validator
    NOT_SORTED_OR_UNIQUE_GUARANTORS = "not_sorted_or_unique_guarantors"  # work Report's guarantee Validators are not sorted
    BAD_CORE_INDEX = "bad_core_index" # core index in not exist
    DUPLICATE_PACKAGE_IN_REPORT = "duplicate_package_in_report" # two same package exist in report
    DUPLICATE_PACKAGE_IN_RECENT_HISTORY = "duplicate_package_in_recent_history" # work package exist in recent block
    OUT_OF_ORDER_GUARANTEE = "out_of_order_guarantee" # core-index not in order
    TOO_MANY_DEPENDENCIES = "too_many_dependencies" # work package has may dependencies
    ANCHOR_NOT_RECENT = "anchor_not_recent" # anchor not present in recent blocks
    BAD_CODE_HASH = "bad_code_hash"
    BAD_STATE_ROOT = "bad_state_root"
    BAD_BEEFY_MMR_ROOT = "bad_beefy_mmr_root"
    BAD_SERVICE_ID = "bad_service_id"
    CORE_ENGAGED = "core_engaged"
    DEPENDENCY_MISSING = "dependency_missing"
    DUPLICATE_PACKAGE = "duplicate_package"
    FUTURE_REPORT_SLOT = "future_report_slot"
    INSUFFICIENT_GURANTEE = "insufficient_guarantees"
    SERVICE_ITEM_GAS_TOO_LOW = "service_item_gas_too_low"
    SEGMENT_ROOT_LOOKUP_INVALID= "segment_root_lookup_invalid"
    WORK_REPORT_GAS_TOO_HIGH= "work_report_gas_too_high"
    REPORT_EPOCH_BEFORE_LAST="report_epoch_before_last"
    WORK_REPORT_TOO_BIG = "work_report_too_big"
    WRONG_ASSIGNMENT = "wrong_assignment"
