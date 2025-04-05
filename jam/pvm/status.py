from dataclasses import dataclass
from jam.types.base.choices.option import decodable_option
from jam.types.base.enum import Enum, decodable_enum
from jam.types.protocol.core import Register
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass

@decodable_enum
class ExecutionStatusCode(Enum):
    HALT = "halt"
    PANIC = "panic"
    OUT_OF_GAS = "out-of-gas"
    PAGE_FAULT = "page-fault"
    HOST = "host-call"
    CONTINUE = "continue"


@decodable_option(Register)
class OptionalRegister(Codable):
    ... 

@decodable_dataclass
@dataclass
class ExecutionStatus(Codable):
    code: ExecutionStatusCode
    register: OptionalRegister

# Constructured statuses to use directly
# Panic
PANIC = ExecutionStatus(ExecutionStatusCode.PANIC, OptionalRegister(None))
# Page fault with a register value
def PAGE_FAULT(register: Register) -> ExecutionStatus:
    return ExecutionStatus(ExecutionStatusCode.PAGE_FAULT, OptionalRegister(register))
# Halt 
HALT = ExecutionStatus(ExecutionStatusCode.HALT, OptionalRegister(None))
# Host call with a register value
def HOST(register: Register) -> ExecutionStatus:
    return ExecutionStatus(ExecutionStatusCode.HOST, OptionalRegister(register))
# Out of gas
OUT_OF_GAS = ExecutionStatus(ExecutionStatusCode.OUT_OF_GAS, OptionalRegister(None))
# Continue
CONTINUE = ExecutionStatus(ExecutionStatusCode.CONTINUE, OptionalRegister(None))
