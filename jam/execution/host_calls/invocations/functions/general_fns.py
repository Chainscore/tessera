from typing import Any, Optional, List

from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.host_calls.invocations.protocol import Context, DispatchNormalReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus, PANIC, HostStatus, CONTINUE, PvmError
from jam.types.base import U64, U32, U16, Bytes, Int
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.state.delta import AccountData
from jam.types.protocol.core import Gas, ServiceId, Register, Balance
from jam.types.state.delta import Delta
from jam.types.work.item import WorkItem
from jam.types.work.package import WorkPackage
from jam.utils.constants import (
    ADDITIONAL_BALANCE_PER_ITEM, SLOT_PERIOD, MAX_AUTH_QUEUE_ITEMS, ROTATION_PERIOD, MAX_ACCUMULATION_ENTRIES, EXTRINSIC_COUNT,
    UNAVAILABLE_WORK_EXPIRY, VALIDATOR_COUNT, MAX_AUTH_CODE_SIZE, MAX_ENCODED_WORK_PACKAGE_SIZE, MAX_SERVICE_CODE_SIZE, BASIC_ERASURE_SIZE, SEGMENT_SIZE, MAX_IMPORT_ITEM,
    ERASURE_PIECES_PER_SEGMENT, MAX_WORK_REPORT_SIZE, TRANSFER_MEMO_SIZE, MAX_EXPORT_ITEM, CORE_COUNT, PREIMAGE_EVICTION_TIMESLOTS, EPOCH_LENGTH, ACCUMULATION_GAS,
    IS_AUTHORIZED_GAS, REFINE_GAS, TOTAL_GAS, RECENT_HISTORY_SIZE, MAX_WORK_ITEMS, MAX_DEPENDENCIES, LOOKUP_ANCHOR_MAX_AGE,
    MAX_AUTH_POOL_ITEMS, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, TICKET_SUBMISSION_END,
)


class GeneralFunctions(INVF):

    @staticmethod
    @INVF.register(0, gas_cost=10)
    def gas(gas: Gas, registers: Registers, memory: Memory, context: Context) -> DispatchNormalReturn:
        registers[7] = gas
        return ExecutionStatus.CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(1, gas_cost=10)
    def lookup(
            gas: Gas,
            registers: Registers,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId,
            accounts: Delta
    ):
        a: None|AccountData = None
        if service_index <= registers[7] <= 2**64-1:
            a = service_data
        elif registers[7] in accounts:
            a = accounts[registers[7]]
        h, o = registers[8], registers[9]

        if not memory.is_accessible(h, 32):
            raise PvmError(PANIC)

        v: None|Bytes = None
        data = memory.read(int(h), 32)
        if a is not None:
            # Directly get data, returns None if not found
            v = a.lookup.get(OpaqueHash(data))

        f = min(int(registers[10]), len(v))
        l = min(int(registers[11]), len(v) - f)

        if not memory.is_accessible(o, l):
            raise PvmError(PANIC)

        if v is None:
            registers[7] = HostStatus.NONE
        else:
            registers[7] = Register(len(v))
            memory.write(o, memory.read(f, l))
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=18, gas_cost=10)
    def fetch(
            gas: Gas,
            registers: Registers,
            memory: Memory,
            context: Optional[Any],
            package: WorkPackage,
            entropy: OpaqueHash,
            trace: Bytes,
            item_index: int,
            import_segments: Optional[List],
            extrinsics: Optional[List],
            o: Optional[List],
            t: Optional[List]
        ):
        w10 = registers[10]
        w11 = registers[11]
        w12 = registers[12]
        v = None
        if w10 == 0:
            v = (
                U64(ADDITIONAL_BALANCE_PER_ITEM).encode() + U64(ADDITIONAL_BALANCE_PER_OCTET).encode() + U64(BASIC_MINIMUM_BALANCE).encode() + U16(CORE_COUNT).encode() +
                U32(PREIMAGE_EVICTION_TIMESLOTS).encode() + U32(EPOCH_LENGTH).encode() + U64(ACCUMULATION_GAS).encode() + U64(IS_AUTHORIZED_GAS).encode() +
                U64(REFINE_GAS).encode() + U64(TOTAL_GAS).encode() + U16(RECENT_HISTORY_SIZE).encode() + U16(MAX_WORK_ITEMS).encode() + U16(MAX_DEPENDENCIES).encode() +
                U32(LOOKUP_ANCHOR_MAX_AGE).encode() + U16(MAX_AUTH_POOL_ITEMS).encode() + U16(SLOT_PERIOD).encode() + U16(MAX_AUTH_QUEUE_ITEMS).encode() +
                U16(ROTATION_PERIOD).encode() + U16(MAX_ACCUMULATION_ENTRIES).encode() + U16(EXTRINSIC_COUNT).encode() + U16(UNAVAILABLE_WORK_EXPIRY).encode() +
                U16(VALIDATOR_COUNT).encode() + U32(MAX_AUTH_CODE_SIZE).encode() + U32(MAX_ENCODED_WORK_PACKAGE_SIZE).encode() + U32(MAX_SERVICE_CODE_SIZE).encode() +
                U32(BASIC_ERASURE_SIZE).encode() + U32(SEGMENT_SIZE).encode() + U32(MAX_IMPORT_ITEM).encode() + U32(ERASURE_PIECES_PER_SEGMENT).encode() +
                U32(MAX_WORK_REPORT_SIZE).encode() + U32(TRANSFER_MEMO_SIZE).encode() + U32(MAX_EXPORT_ITEM).encode() + U32(TICKET_SUBMISSION_END).encode()
            )
        elif w10 == 1 and entropy is not None:
            v = entropy
        elif w10 == 2 and trace is not None:
            v = trace
        elif item_index is not None:
            if w10 == 3 and w11 < len(extrinsics) and w12 < len(extrinsics[int(w11)]):
                v = extrinsics[w11][int(w12)]
            elif w10 == 4 and w11 < len(extrinsics[item_index]):
                v = extrinsics[item_index][w11]
            elif w10 == 5 and w11 < len(import_segments) and w12 < len(import_segments[w11]):
                v = import_segments[w11][w12]
            elif w10 == 6 and w11 < len(import_segments[item_index]):
                v = import_segments[item_index][w11]
        elif package is not None:
            def s_cap(w: WorkItem):
                return (w.service.encode() +
                        bytes(w.code_hash) +
                        w.refine_gas_limit.encode() +
                        w.accumulate_gas_limit.encode() +
                        w.export_count.encode() +
                        U16(len(w.import_segments)).encode() +
                        U16(len(w.extrinsic)).encode() +
                        U32(len(w.payload))
                        )
            if w10 == 7:
                v = package.encode()
            elif w10 == 8:
                v = package.code_hash + package.params
            elif w10 == 9:
                v = package.authorization
            elif w10 == 10:
                v = package.context.encode()
            elif w10 == 11:
                v = b""
                for item in package.items:
                    v += s_cap(item)
            elif w10 == 12 and w11 < len(package.items):
                v = s_cap(package.items[w11])
            elif w10 == 13 and w11 < len(package.items):
                v = package.items[w11].payload
        elif o is not None:
            if w10 == 14:
                v = o.encode()
            elif w10 == 15 and w11 < len(o):
                v = o[w11]
        elif t is not None:
            if w10 == 16:
                v = t.encode()
            elif w10 == 17 and w11 < len(t):
                v = t[w11]

        if v is None:
            registers[7] = HostStatus.NONE.value
            return CONTINUE, gas, registers, memory, context

        memory_start = int(registers[7])
        f = min(int(registers[8]), len(v))
        l = min(int(registers[9]), len(v) - f)

        if not memory.is_accessible(memory_start, l, for_write=True):
            print("Memory not accessible", memory_start, l)
            raise PvmError(PANIC)

        registers[7] = Register(len(v))
        print(f"Writing {v[f:l]} to {memory_start}")
        memory.write(memory_start, v[f:l])
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=2, gas_cost=10)
    def read(
            gas: Gas,
            registers: Registers,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId,
            accounts: Delta
    ):
        s_star = ServiceId(registers[7])
        if s_star == 2**64 - 1:
            s_star = service_index

        a: None|AccountData = None
        if s_star == service_index:
            a = service_data
        elif s_star in accounts:
            a = accounts[s_star]
        ko, kz, o = registers[8], registers[9], registers[10]

        if not memory.is_accessible(ko, kz - ko):
            raise PvmError(PANIC)

        v: None|Bytes = None
        k = Hash.blake2b(s_star.encode() + memory.read(ko, kz - ko))

        if a is not None:
            # Directly get data, returns None if not found
            v = a.storage.get(k)

        f = min(int(registers[11]), len(v))
        l = min(int(registers[12]), len(v) - f)

        if not memory.is_accessible(o, l):
            raise PvmError(PANIC)

        if v is None:
            registers[7] = HostStatus.NONE
        else:
            registers[7] = Register(len(v))
            memory.write(o, memory.read(f, l))
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=3, gas_cost=10)
    def write(
            gas: Gas,
            registers: Registers,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId
    ):
        # Get key,value start,end
        [ko, kz, vo, vz] = registers[7: 7+4]
        ko, kz, vo, vz = int(ko), int(kz), int(vo), int(vz)
        if not memory.is_accessible(ko, kz):
            raise PvmError(PANIC)

        k = Hash.blake2b(service_index.encode() + memory.read(ko, kz))

        if not memory.is_accessible(vo, vz):
            raise PvmError(PANIC)
        a = service_data.storage
        if vz == 0:
            del a[k]
        else:
            try:
                a[k] = Bytes(memory.read(vo, vz))
            except PvmError:
                # TODO - Handle ONLY storage full
                registers[7] = HostStatus.FULL
                return CONTINUE, gas, registers, memory, service_data

        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=4, gas_cost=10)
    def info(
            gas: Gas,
            registers: Registers,
            memory: Memory,
            context: Optional[Any],
            service_index: ServiceId,
            accounts: Delta
    ):
        t = accounts[registers[7]]
        if registers[7] == 2**64 - 1:
            t = accounts[service_index]

        o = registers[8]
        if t is not None:
            m = t.code_hash.encode() + t.balance.encode() + Balance(t.t).encode() + t.gas_limit.encode() + t.min_gas.encode() + t.num_o.encode() + t.num_i.encode()
            if memory.is_accessible(o, len(m), True):
                registers[7] = HostStatus.OK
                memory.write(o, m)
            else:
                raise PvmError(PANIC)
        else:
            registers[7] = HostStatus.NONE

        return CONTINUE, gas, registers, memory, context