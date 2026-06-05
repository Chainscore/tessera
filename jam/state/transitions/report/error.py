from jam.error import JamError
from tsrkit_types.enum import Enum


class ReportingError(JamError):
    ...


class ReportingErrorCode(Enum):
    """Error codes for the Reporting"""

    CORE_UNAUTHORIZED = "core_unauthorized"
    BAD_VALIDATOR_INDEX = "bad_validator_index"
    NOT_ENOUGH_GUARANTEE = "not_enough_guarantee"
    NOT_SORTED_OR_UNIQUE_GUARANTORS = "not_sorted_or_unique_guarantors"
    BAD_CORE_INDEX = "bad_core_index"
    DUPLICATE_PACKAGE_IN_RECENT_HISTORY = "duplicate_package_in_recent_history"
    OUT_OF_ORDER_GUARANTEE = "out_of_order_guarantee"
    TOO_MANY_DEPENDENCIES = "too_many_dependencies"
    ANCHOR_NOT_RECENT = "anchor_not_recent"
    BAD_ANCHOR_SLOT = "anchor_slot_mismatch"
    BAD_CODE_HASH = "bad_code_hash"
    BAD_STATE_ROOT = "bad_state_root"
    BAD_BEEFY_MMR_ROOT = "bad_beefy_mmr_root"
    BAD_SERVICE_ID = "bad_service_id"
    CORE_ENGAGED = "core_engaged"
    DEPENDENCY_MISSING = "dependency_missing"
    DUPLICATE_PACKAGE = "duplicate_package"
    FUTURE_REPORT_SLOT = "future_report_slot"
    INSUFFICIENT_GUARANTEE = "insufficient_guarantees"
    MISSING_WORK_RESULTS = "missing_work_results"
    SERVICE_ITEM_GAS_TOO_LOW = "service_item_gas_too_low"
    SEGMENT_ROOT_LOOKUP_INVALID = "segment_root_lookup_invalid"
    WORK_REPORT_GAS_TOO_HIGH = "work_report_gas_too_high"
    REPORT_EPOCH_BEFORE_LAST = "report_epoch_before_last"
    WORK_REPORT_TOO_BIG = "work_report_too_big"
    WRONG_ASSIGNMENT = "wrong_assignment"
    BAD_SIGNATURE = "bad_signature"
    BANNED_VALIDATOR = "banned_validator"
