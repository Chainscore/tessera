from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum

class ErasureCodingError(JamError):
    ...

@decodable_enum
class ErasureCodingErrorCode(Enum):
    BAD_ERASURE = ""
    BAD_IMPORT_MESSAGE = ""
    BAD_MESSAGE = ""
