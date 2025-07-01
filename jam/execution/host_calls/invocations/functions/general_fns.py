from typing import Any, Optional, List

from jam.logging import get_logger
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.host_calls.invocations.protocol import Context, DispatchNormalReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import ExecutionStatus, PANIC, HostStatus, CONTINUE, PvmError
from tsrkit_types import U64, U32, U16, Bytes, Uint
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.state.delta import AccountData
from jam.types.protocol.core import Gas, ServiceId, Register
from jam.types.state.delta import Delta
from jam.types.work import WorkItem
from jam.types.work import WorkPackage
from jam.utils.constants import (
    ADDITIONAL_BALANCE_PER_ITEM, SLOT_PERIOD, MAX_AUTH_QUEUE_ITEMS, ROTATION_PERIOD, MAX_ACCUMULATION_ENTRIES, EXTRINSIC_COUNT,
    UNAVAILABLE_WORK_EXPIRY, VALIDATOR_COUNT, MAX_AUTH_CODE_SIZE, MAX_ENCODED_WORK_PACKAGE_SIZE, MAX_SERVICE_CODE_SIZE, BASIC_ERASURE_SIZE, SEGMENT_SIZE, MAX_IMPORT_ITEM,
    ERASURE_PIECES_PER_SEGMENT, MAX_WORK_REPORT_SIZE, TRANSFER_MEMO_SIZE, MAX_EXPORT_ITEM, CORE_COUNT, PREIMAGE_EVICTION_TIMESLOTS, EPOCH_LENGTH, ACCUMULATION_GAS,
    IS_AUTHORIZED_GAS, REFINE_GAS, TOTAL_GAS, RECENT_HISTORY_SIZE, MAX_WORK_ITEMS, MAX_DEPENDENCIES, LOOKUP_ANCHOR_MAX_AGE,
    MAX_AUTH_POOL_ITEMS, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, TICKET_SUBMISSION_END,
)

# Module-specific logger
logger = get_logger("host_calls")


class GeneralFunctions(INVF):

    @staticmethod
    @INVF.register(0, gas_cost=10)
    def gas(gas: Gas, registers: list, memory: Memory, context: Context) -> DispatchNormalReturn:
        logger.debug(
            "Host call: gas",
            gas_remaining=gas,
            gas_value_returned=gas
        )
        registers[7] = gas
        return ExecutionStatus.CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(1, gas_cost=10)
    def lookup(
            gas: Gas,
            registers: list,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId,
            accounts: Delta
    ):
        lookup_key = registers[7]
        hash_addr = registers[8]
        output_addr = registers[9]
        
        logger.debug("Host call: lookup", lookup_key=lookup_key, hash_addr=hash_addr, output_addr=output_addr, service_index=int(service_index))
        
        a: None|AccountData = None
        if service_index <= lookup_key <= 2**64-1:
            a = service_data
        elif lookup_key in accounts:
            a = accounts[lookup_key]

        if not memory.is_accessible(hash_addr, 32):
            logger.error(
                "Host call lookup: memory not accessible for hash",
                hash_addr=hash_addr,
                required_size=32
            )
            raise PvmError(PANIC)

        v: None|Bytes = None
        data = memory.read(int(hash_addr), 32)
        if a is not None:
            # Directly get data, returns None if not found
            v = a.lookup.get(OpaqueHash(data))

        f = min(int(registers[10]), len(v) if v else 0)
        l = min(int(registers[11]), (len(v) if v else 0) - f)

        if not memory.is_accessible(output_addr, l):
            logger.error(
                "Host call lookup: memory not accessible for output",
                output_addr=output_addr,
                required_size=l
            )
            raise PvmError(PANIC)

        if v is None:
            registers[7] = HostStatus.NONE
            logger.debug(
                "Host call lookup: value not found",
                lookup_key=lookup_key,
                hash_hex=data.hex()[:16] + "..."
            )
        else:
            registers[7] = Register(len(v))
            memory.write(output_addr, memory.read(f, l))
            logger.debug(
                "Host call lookup: value found",
                lookup_key=lookup_key,
                value_length=len(v),
                returned_length=l
            )
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=18, gas_cost=10)
    def fetch(
            gas: Gas,
            registers: list,
            memory: Memory,
            context: Optional[Any],
            package: Optional[WorkPackage],
            entropy: Optional[OpaqueHash],
            trace: Optional[Bytes],
            item_index: int,
            import_segments: Optional[List],
            extrinsics: Optional[List],
            o: Optional[List],
            t: Optional[List]
        ):
        fetch_type = registers[10]
        
        logger.debug("Host call: fetch", fetch_type=fetch_type, item_index=item_index)
        
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
            logger.debug("Fetch: returning system constants")
        elif w10 == 1 and entropy is not None:
            v = entropy
            logger.debug("Fetch: returning entropy")
        elif w10 == 2 and trace is not None:
            v = trace
            logger.debug("Fetch: returning trace")
        elif w10 == 3 and item_index is not None and w11 < len(extrinsics) and w12 < len(extrinsics[int(w11)]):
            v = extrinsics[w11][int(w12)]
            logger.debug("Fetch: returning extrinsic data", w11=w11, w12=w12)
        elif w10 == 4 and item_index is not None and w11 < len(extrinsics[item_index]):
            v = extrinsics[item_index][w11]
            logger.debug("Fetch: returning item extrinsic", item_index=item_index, w11=w11)
        elif w10 == 5 and item_index is not None and w11 < len(import_segments) and w12 < len(import_segments[w11]):
            v = import_segments[w11][w12]
            logger.debug("Fetch: returning import segment", w11=w11, w12=w12)
        elif w10 == 6 and item_index is not None and w11 < len(import_segments[item_index]):
            v = import_segments[item_index][w11]
            logger.debug("Fetch: returning item import segment", item_index=item_index, w11=w11)
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
                logger.debug("Fetch: returning package data")
            elif w10 == 8:
                v = package.authorizer.code_hash + package.authorizer.params
                logger.debug("Fetch: returning authorizer data")
            elif w10 == 9:
                v = package.authorization
                logger.debug("Fetch: returning authorization")
            elif w10 == 10:
                v = package.context.encode()
                logger.debug("Fetch: returning context")
            elif w10 == 11:
                v = b""
                for item in package.items:
                    v += s_cap(item)
                logger.debug("Fetch: returning all item summaries", item_count=len(package.items))
            elif w10 == 12 and w11 < len(package.items):
                v = s_cap(package.items[w11])
                logger.debug("Fetch: returning item summary", item_index=w11)
            elif w10 == 13 and w11 < len(package.items):
                v = package.items[w11].payload
                logger.debug("Fetch: returning item payload", item_index=w11)
        elif o is not None:
            if w10 == 14:
                v = o.encode()
                logger.debug("Fetch: returning o data")
            elif w10 == 15 and w11 < len(o):
                v = o[w11]
                logger.debug("Fetch: returning o item", index=w11)
        elif t is not None:
            if w10 == 16:
                v = t.encode()
                logger.debug("Fetch: returning t data")
            elif w10 == 17 and w11 < len(t):
                v = t[w11]
                logger.debug("Fetch: returning t item", index=w11)

        if v is None:
            registers[7] = HostStatus.NONE.value
            logger.debug("Fetch: no data found for request", fetch_type=w10)
            return CONTINUE, gas, registers, memory, context

        memory_start = int(registers[7])
        f = min(int(registers[8]), len(v))
        l = min(int(registers[9]), len(v) - f)

        if not memory.is_accessible(memory_start, l, for_write=True):
            logger.error(
                "Fetch: memory not accessible for write",
                memory_start=memory_start,
                required_size=l
            )
            raise PvmError(PANIC)

        registers[7] = Register(len(v))
        memory.write(memory_start, v[f:l])
        
        logger.debug(
            "Fetch: data written to memory",
            memory_start=memory_start,
            data_length=len(v),
            written_length=l
        )
        
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=2, gas_cost=10)
    def read(
            gas: Gas,
            registers: list,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId,
            accounts: Delta
    ):
        service_key = registers[7]
        key_offset = registers[8]
        key_size = registers[9]
        output_offset = registers[10]
        
        logger.debug("Host call: read", service_key=service_key, key_offset=key_offset, key_size=key_size, output_offset=output_offset)
        
        if service_key == 2**64 - 1:
            s_star = service_index
        else:
            s_star = ServiceId(service_key)

        a: None|AccountData = None
        if s_star == service_index:
            a = service_data
        elif s_star in accounts:
            a = accounts[s_star]
            
        key_start, key_len, o = registers[8:8+3]

        if not memory.is_accessible(key_start, key_len):
            logger.error("Host call read: memory not accessible for key", key_offset=ko, key_size=kz)
            raise PvmError(PANIC)

        value: None|Bytes = None
        key = Hash.blake2b(s_star.encode() + memory.read(key_start, key_len))

        if a is not None:
            # Directly get data, returns None if not found
            value = a.storage[key]

        if value is None or len(value) == 0:
            registers[7] = HostStatus.NONE.value
            logger.debug("Host call read: storage value not found", service_key=service_key, storage_key=key.hex()[:16] + "...")
        else:
            start = min(int(registers[11]), len(value))
            length = min(int(registers[12]), len(value) - start)

            if not memory.is_accessible(o, length, for_write=True):
                logger.error( "Host call read: memory not accessible for output", output_offset=o, required_size=l)
                raise PvmError(PANIC)
            registers[7] = Register(len(value))
            memory.write(o, value[start:start+length])
            
            logger.debug("Host call read: storage value found", service_key=service_key, value_length=len(value), returned_length=length)
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=3, gas_cost=10)
    def write(
            gas: Gas,
            registers: list,
            memory: Memory,
            context: Optional[Any],
            service_data: AccountData,
            service_index: ServiceId
    ):
        # Get key,value start,end
        [ko, kz, vo, vz] = registers[7: 7+4]
        
        logger.debug("Host call: write", key_offset=ko, key_size=kz, value_offset=vo, value_size=vz, service_index=int(service_index))
        
        if not memory.is_accessible(ko, kz):
            logger.error(
                "Host call write: memory not accessible for key",
                key_offset=ko,
                key_size=kz
            )
            raise PvmError(PANIC)

        k = Hash.blake2b(service_index.encode() + memory.read(ko, kz))

        a = service_data.storage

        curr_value = a[k]
        storage_len = len(curr_value) if curr_value else HostStatus.NONE.value
        if vz == 0:
            a.__delitem__(k)
            logger.debug(
                "Host call write: storage key deleted",
                storage_key=k.hex()[:16] + "..."
            )
        else:
            if not memory.is_accessible(vo, vz):
                logger.error(
                    "Host call write: memory not accessible for value",
                    value_offset=vo,
                    value_size=vz
                )
                raise PvmError(PANIC)
            try:
                a[k] = Bytes(memory.read(vo, vz))
                logger.debug(
                    "Host call write: storage updated",
                    storage_key=k.hex()[:16] + "...",
                    value_size=vz
                )
            except PvmError:
                # TODO - Handle ONLY storage full
                registers[7] = HostStatus.FULL.value
                logger.warning(
                    "Host call write: storage full",
                    storage_key=k.hex()[:16] + "..."
                )
                return CONTINUE, gas, registers, memory, service_data

        registers[7] = storage_len
        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(host_call=4, gas_cost=10)
    def info(
            gas: Gas,
            registers: list,
            memory: Memory,
            context: Optional[Any],
            service_index: ServiceId,
            accounts: Delta
    ):
        target_service = registers[7]
        output_offset = registers[8]
        
        logger.debug(
            "Host call: info",
            target_service=target_service,
            output_offset=output_offset,
            service_index=int(service_index)
        )
        
        if target_service == 2**64 - 1:
            t = accounts[service_index]
        else:
            t = accounts[ServiceId(target_service)]

        o = registers[8]

        if t is not None:
            m = bytes(t.service.code_hash) + Uint(t.service.balance).encode() + Uint(t.service.t).encode() + Uint(t.service.gas_limit).encode() + Uint(t.service.min_gas).encode() + Uint(t.service.num_o).encode() + Uint(t.service.num_i).encode()

            if memory.is_accessible(o, len(m), True):
                registers[7] = HostStatus.OK.value
                memory.write(o, m)
                logger.debug(
                    "Host call info: service info written",
                    target_service=target_service,
                    info_size=len(m)
                )
            else:
                logger.error(
                    "Host call info: memory not accessible",
                    output_offset=o,
                    required_size=len(m)
                )
                raise PvmError(PANIC)
        else:
            registers[7] = HostStatus.NONE.value
            logger.debug(
                "Host call info: service not found",
                target_service=target_service
            )

        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(host_call=100, gas_cost=0)
    def log(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        core_index: int,
        service_id: int
    ):
        message_start = registers[10]
        message_length = registers[11]

        target_start = registers[8]
        target_length = registers[9]

        level = registers[7]
        
        # Validate memory accessibility for message
        if not memory.is_accessible(message_start, message_length):
            logger.error(
                "Host call log: memory not accessible for message",
                message_start=message_start,
                message_length=message_length,
            )
            raise PvmError(PANIC)

        if target_length != 0 or target_start != 0:
            if not memory.is_accessible(target_start, target_length):
                logger.error(
                    "Host call log: memory not accessible for target",
                    target_start=target_start,
                    target_length=target_length,
                )
                raise PvmError(PANIC)
            target_bytes = memory.read(int(target_start), int(target_length))
            try:
                target_str = target_bytes.decode("utf-8", errors="replace")
            except Exception:
                target_str = target_bytes.hex()
        else:
            target_str = None

        message_bytes = memory.read(int(message_start), int(message_length))
        try:
            message_str = message_bytes.decode("utf-8", errors="replace")
        except Exception:
            message_str = message_bytes.hex()

        log_kwargs = {"target": target_str, "level": int(level), "core_index": core_index, "service_id": service_id}

        # Load the default logger
        jam_logger = get_logger()
        if int(level) == 0:
            jam_logger.error(message_str, **log_kwargs)
        elif int(level) == 1:
            jam_logger.warning(message_str, **log_kwargs)
        elif int(level) == 2:
            jam_logger.info(message_str, **log_kwargs)
        else:
            jam_logger.debug(message_str, **log_kwargs)

        return CONTINUE, gas, registers, memory, context