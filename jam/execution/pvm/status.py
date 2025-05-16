from dataclasses import dataclass
from jam.types.base.choices.option import Option, decodable_option
from jam.types.base.enum import Enum, decodable_enum
from jam.types.base.integers.fixed import U64, U8
from jam.types.base.null import Null
from jam.types.protocol.core import Register
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.error import JamError

@decodable_option(Register)
class OptionalRegister(Option):
    ...

@decodable_dataclass
@dataclass
class ExecValue(Codable):
    code: U8
    register: OptionalRegister


@decodable_enum
class ExecutionStatus(Enum):
    HALT         = ExecValue(U8(0), OptionalRegister(Null))
    PANIC        = ExecValue(U8(1), OptionalRegister(Null))
    PAGE_FAULT   = ExecValue(U8(2), OptionalRegister(Null))
    HOST         = ExecValue(U8(3), OptionalRegister(Null))
    OUT_OF_GAS   = ExecValue(U8(4), OptionalRegister(Null))
    CONTINUE     = ExecValue(U8(5), OptionalRegister(Null))

@decodable_enum
class HostStatus(Enum):
    NONE    = U64(2**64 - 1)
    WHAT    = U64(2**64 - 2)
    OOB     = U64(2**64 - 3)
    WHO     = U64(2**64 - 4)
    FULL    = U64(2**64 - 5)
    CORE    = U64(2**64 - 6)
    CASH    = U64(2**64 - 7)
    LOW     = U64(2**64 - 8)
    HUH     = U64(2**64 - 9)
    OK      = U64(0)


# Constructured statuses to use directly
# Panic
PANIC = ExecutionStatus.PANIC
# Page fault with a register value
def PAGE_FAULT(register: Register) -> ExecutionStatus:
    result = ExecutionStatus.PAGE_FAULT
    result.value.register = OptionalRegister(register)
    return result
# Halt
HALT = ExecutionStatus.HALT
# Host call with a register value
def HOST(register: Register) -> ExecutionStatus:
    result = ExecutionStatus.HOST
    result.value.register = OptionalRegister(register)
    return result
# Out of gas
OUT_OF_GAS = ExecutionStatus.OUT_OF_GAS
# Continue
CONTINUE = ExecutionStatus.CONTINUE

class PvmError(JamError):
    ...
