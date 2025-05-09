from jam.execution.host_calls._types import refine_context
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.host_calls.invocations.protocol import Context, DispatchNormalReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus, PANIC, HostStatus, CONTINUE
from jam.types import Bytes, ByteArray32, OpaqueHash, WorkPackage, U64, U32, U16
from jam.types.state.delta import AccountData
from jam.state.state import state
from jam.types.protocol.core import Gas, ServiceId, Register
from jam.types.state import Delta
from jam.utils.codec.primitives import IntegerCodec
from jam.utils.constants import (
    ADDITIONAL_BALANCE_PER_ITEM,
    SLOT_PERIOD,
    MAX_AUTH_QUEUE_ITEMS,
    ROTATION_PERIOD,
    MAX_ACCUMULATION_ENTRIES,
    EXTRINSIC_COUNT,
    UNAVAILABLE_WORK_EXPIRY,
    VALIDATOR_COUNT,
    MAX_AUTH_CODE_SIZE,
    MAX_ENCODED_WORK_PACKAGE_SIZE,
    MAX_SERVICE_CODE_SIZE,
    BASIC_ERASURE_SIZE,
    SEGMENT_SIZE,
    MAX_IMPORT_ITEM,
    ERASURE_PIECES_PER_SEGMENT,
    MAX_WORK_REPORT_SIZE,
    TRANSFER_MEMO_SIZE,
    MAX_EXPORT_ITEM,
    CORE_COUNT,
    PREIMAGE_EVICTION_TIMESLOTS,
    EPOCH_LENGTH,
    ACCUMULATION_GAS,
    IS_AUTHORIZED_GAS,
    REFINE_GAS,
    TOTAL_GAS,
    RECENT_HISTORY_SIZE,
    MAX_WORK_ITEMS,
    MAX_DEPENDENCIES,
    LOOKUP_ANCHOR_MAX_AGE,
    MAX_AUTH_POOL_ITEMS, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, TICKET_SUBMISSION_END,
)


class GeneralFunctions(INVF):

    @INVF.register(0, gas_cost=10)
    def gas(cls, gas: Gas, registers: Registers, memory: Memory, context: Context) -> DispatchNormalReturn:
        registers[7] = gas
        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @INVF.register(1, gas_cost=10)
    def lookup(cls, gas: Gas, registers: Registers, memory: Memory, service_data: AccountData, service_index: ServiceId, accounts: Delta):
        a: None|AccountData = None
        if service_index <= registers[7] <= 2**64-1:
            a = service_data
        elif registers[7] in state.delta:
            a = accounts[registers[7]]
        h, o = registers[8], registers[9]

        if not memory.is_accessible(h, 32):
            raise PANIC

        v: None|Bytes = None
        data = memory.read(int(h), 32)
        if a is not None:
            # Directly get data, returns None if not found
            v = a.lookup.get(OpaqueHash(data))

        f = min(int(registers[10]), len(v))
        l = min(int(registers[11]), len(v) - f)

        if not memory.is_accessible(o, l):
            raise PANIC

        if v is None:
            registers[7] = HostStatus.NONE
        else:
            registers[7] = Register(len(v))
            memory.write(o, memory.read(f, l))
        return CONTINUE, gas, registers, memory

    @INVF.register(host_call=18, gas_cost=10)
    def fetch(
        cls,
        gas: Gas,
        registers: Register,
        memory: Memory,
        context: refine_context,
        package: WorkPackage,
        n: OpaqueHash,
        r: OpaqueHash,
        i: int,
        i_bar,
        x_bar,
        o,
        t
    ):
        w10 = registers[10]
        w11 = registers[11]
        w12 = registers[12]
        v = None
        if w10 == 0:
            v = (
                U64(ADDITIONAL_BALANCE_PER_ITEM).encode() +
                U64(ADDITIONAL_BALANCE_PER_OCTET).encode() +
                U64(BASIC_MINIMUM_BALANCE).encode() +
                U16(CORE_COUNT).encode() +
                U32(PREIMAGE_EVICTION_TIMESLOTS).encode() +
                U32(EPOCH_LENGTH).encode() +
                U64(ACCUMULATION_GAS).encode() +
                U64(IS_AUTHORIZED_GAS).encode() +
                U64(REFINE_GAS).encode() +
                U64(TOTAL_GAS).encode() +
                U16(RECENT_HISTORY_SIZE).encode() +
                U16(MAX_WORK_ITEMS).encode() +
                U16(MAX_DEPENDENCIES).encode() +
                U32(LOOKUP_ANCHOR_MAX_AGE).encode() +
                U16(MAX_AUTH_POOL_ITEMS).encode() +
                U16(SLOT_PERIOD).encode() +
                U16(MAX_AUTH_QUEUE_ITEMS).encode() +
                U16(ROTATION_PERIOD).encode() +
                U16(MAX_ACCUMULATION_ENTRIES).encode() +
                U16(EXTRINSIC_COUNT).encode() +
                U16(UNAVAILABLE_WORK_EXPIRY).encode() +
                U16(VALIDATOR_COUNT).encode() +
                U32(MAX_AUTH_CODE_SIZE).encode() +
                U32(MAX_ENCODED_WORK_PACKAGE_SIZE).encode() +
                U32(MAX_SERVICE_CODE_SIZE).encode() +
                U32(BASIC_ERASURE_SIZE).encode() +
                U32(SEGMENT_SIZE).encode() +
                U32(MAX_IMPORT_ITEM).encode() +
                U32(ERASURE_PIECES_PER_SEGMENT).encode() +
                U32(MAX_WORK_REPORT_SIZE).encode() +
                U32(TRANSFER_MEMO_SIZE).encode() +
                U32(MAX_EXPORT_ITEM).encode() +
                U32(TICKET_SUBMISSION_END).encode()
            )
        elif w10 == 1 and n is not None:
            v = n
        elif w10 == 2 and r is not None:
            v = r
        elif i is not None:
            if w10 == 3 and w11 < len(x_bar) and w12 < len(x_bar[int(w11)]):
                v = x_bar[w11][int(w12)]
            elif w10 == 4 and w11 < len(x_bar[i]):
                v = x_bar[i][w11]
            elif w10 == 5 and w11 < len(i_bar) and w12 < len(i_bar[w11]):
                v = i_bar[w11][w12]
            elif w10 == 6 and w11 < len(i_bar[i]):
                v = i_bar[i][w11]
        elif package is not None:
            if w10 == 7:
                v = package.encode()
            elif w10 == 8:
                v = package.code_hash + package.params
            elif w10 == 9:
                v = package.authorization
            elif w10 == 10:
                x = package.context.encode()
            elif w10 == 11:

            elif w10 == 12
            elif w10 == 13
