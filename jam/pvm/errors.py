from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum

class PvmError(JamError):
    ...

@decodable_enum
class PvmErrorCodes(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"
    HOST = "host-call"
    OUT_OF_GAS = "out-of-gas"
    CONTINUE = "continue"
    # We'll add more as we go
