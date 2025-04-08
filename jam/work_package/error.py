from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum

class WorkPackageError(JamError):
    ...

@decodable_enum
class WorkPackagesErrorCode(Enum):
    BAD_EXPORT_ITEM = ""
    BAD_IMPORT_ITEM = ""
    BAD_EXTRINSIC_COUNT = ""



