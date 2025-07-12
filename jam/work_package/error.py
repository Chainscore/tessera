from jam.error import JamError
from tsrkit_types.enum import Enum


class WorkPackageError(JamError): ...


class WorkPackagesErrorCode(Enum):
    BAD_EXPORT_ITEM = "bad_export_item"
    BAD_IMPORT_ITEM = "bad_import_item"
    BAD_EXTRINSIC_COUNT = "bad_extrinsic_tem"
    BAD_WORK_PACKAGE_SIZE = "bad_work_package_size"
    BAD_REFINEMENT_GAS = "bad_refinement_gas"
    BAD_ACCUMULATION_GAS = "bad_accumulation_gas"
