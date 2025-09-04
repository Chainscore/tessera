from jam.error import JamError
from tsrkit_types.enum import Enum


class ValidatorError(JamError):
    ...


class ValidatorErrorCode(Enum):
    BAD_EXPORT_ITEM = "bad_export_item"
    BAD_IMPORT_ITEM = "bad_import_item"
    BAD_EXTRINSIC_COUNT = "bad_extrinsic_tem"
    BAD_WORK_PACKAGE_SIZE = "bad_work_package_size"
    BAD_REFINEMENT_GAS = "bad_refinement_gas"
    BAD_ACCUMULATION_GAS = "bad_accumulation_gas"


class BundlerError(JamError):
    ...


class BundlerErrorCode(Enum):
    UNKNOWN_ROOT = "Unrecognized root"
    SHARDS_UNAVAILABLE = "Shards not available"
    SEG_ERROR = "Unable to fetch import segments"
    JFN_ERROR = "Unable to fetch justification"
    EXT_ERROR = "Unable to fetch extrinsics"
    LOOKUP_ERROR = "Package hash not found in segment root lookup"


class ProcessorError(JamError):
    ...


class ProcessorErrorCode(Enum):
    INVALID_SIGN = "Invalid Guarantor Signature"
    INSUFFICIENT_GUARANTEES = "Insufficient guarantees for generated work report"
