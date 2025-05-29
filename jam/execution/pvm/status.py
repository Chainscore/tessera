from dataclasses import dataclass
from typing import Optional

from jam.types.base import String
from jam.types.base.composite.option import Option, decodable_option
from jam.types.base.enum import Enum, decodable_enum
from jam.types.base.integers.fixed import U64, U8
from jam.types.base.null import Null
from jam.types.protocol.core import Register
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.error import JamError

@dataclass
class ExecValue(Codable):
    name: str
    code: int
    register: Optional[int]


@decodable_enum
class ExecutionStatus(Enum):
    HALT         = ExecValue("halt", 0 , None)
    PANIC        = ExecValue("panic", 1, None)
    PAGE_FAULT   = ExecValue("page-fault", 2, None)
    HOST         = ExecValue("host", 3, None)
    OUT_OF_GAS   = ExecValue("out-of-gas", 4, None)
    CONTINUE     = ExecValue("continue", 5, None)

@decodable_enum
class HostStatus(Enum):
    NONE    = 2**64 - 1
    WHAT    = 2**64 - 2
    OOB     = 2**64 - 3
    WHO     = 2**64 - 4
    FULL    = 2**64 - 5
    CORE    = 2**64 - 6
    CASH    = 2**64 - 7
    LOW     = 2**64 - 8
    HUH     = 2**64 - 9
    OK      = 0


# Constructured statuses to use directly
# Panic
PANIC = ExecutionStatus.PANIC
# Page fault with a register value
def PAGE_FAULT(register: int) -> ExecutionStatus:
    result = ExecutionStatus.PAGE_FAULT
    result.value.register = register
    return result
# Halt
HALT = ExecutionStatus.HALT
# Host call with a register value
def HOST(register: int) -> ExecutionStatus:
    result = ExecutionStatus.HOST
    result.value.register = register
    return result
# Out of gas
OUT_OF_GAS = ExecutionStatus.OUT_OF_GAS
# Continue
CONTINUE = ExecutionStatus.CONTINUE

class PvmError(JamError):
    ...
