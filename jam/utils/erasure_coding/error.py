from jam.error import JamError
from tsrkit_types.enum import Enum


class ErasureCodingError(JamError): ...


class ErasureCodingErrorCode(Enum):
    BAD_ERASURE = ""
    BAD_IMPORT_MESSAGE = ""
    BAD_MESSAGE = ""
