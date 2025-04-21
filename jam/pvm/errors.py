from enum import Enum
from jam.error import JamError

class PvmError(JamError):
    ...

class PvmErrorCodes(Enum):
    PANIC = "panic"
    HALT = "halt"
    PAGE_FAULT = "page-fault"
    HOST = "host-call"
    OUT_OF_GAS = "out-of-gas"
    CONTINUE = "continue"
    UNEXPECTED = "unexpected"
    INVALID_OPCODE = "invalid-opcode"