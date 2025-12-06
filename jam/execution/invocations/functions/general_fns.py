from typing import Any, Optional, List

from jam.log_setup import pvm_logger as logger, logger as jam_logger
from jam.execution.invocations.functions.protocol import (
    InvocationFunctions as INVF,
)
from jam.execution.invocations.protocol import Context, DispatchReturn
from jam.types.state.accumulation.types import DeferredTransfers, OperandTuples
from jam.types.work.manifest import Extrinsics
from tsrkit_pvm import (
    Memory,
    ExecutionStatus,
    PANIC,
    HostStatus,
    CONTINUE,
    PvmError,
    Accessibility
)
from tsrkit_types import U64, U32, U16, Bytes, Uint
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.state.delta import AccountData
from jam.types.protocol.core import Gas, ServiceId, Register
from jam.types.state.delta import Delta
from jam.types.work import WorkItem
from jam.types.work import WorkPackage
from jam.utils.constants import (
    B_I,
    B_L,
    B_S,
    C,
    D,
    E,
    G_A,
    G_I,
    G_R,
    G_T,
    H,
    I,
    J,
    K,
    L,
    N,
    O,
    P,
    Q,
    R,
    T,
    U,
    V,
    W_A,
    W_B,
    W_C,
    W_E,
    W_M,
    W_P,
    W_R,
    W_T,
    W_X,
    Y,
    PARAMS_ENCODED
)

class GeneralFunctions(INVF):
    @staticmethod
    @INVF.register(0, gas_cost=10)
    def gas(gas: Gas, registers: list, memory: Memory, context: Context) -> DispatchReturn:
        logger.debug("Host call: gas", gas_remaining=gas, gas_value_returned=gas)
        registers[7] = gas
        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(1, gas_cost=10)
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
        extrinsics: Optional[Extrinsics],
        o: Optional[OperandTuples],
        t: Optional[DeferredTransfers],
    ):
        fetch_type = registers[10]

        logger.debug("Host call: fetch", fetch_type=fetch_type, item_index=item_index)

        w10 = registers[10]
        w11 = registers[11]
        w12 = registers[12]
        v = None
        if w10 == 0:
            v = PARAMS_ENCODED
        elif w10 == 1 and entropy is not None:
            v = entropy
        elif w10 == 2 and trace is not None:
            v = trace
        elif (
            w10 == 3
            and item_index is not None
            and w11 < len(extrinsics)
            and w12 < len(extrinsics[int(w11)])
        ):
            v = extrinsics[w11][int(w12)]
        elif w10 == 4 and item_index is not None and w11 < len(extrinsics[item_index]):
            v = extrinsics[item_index][w11]
        elif (
            w10 == 5
            and item_index is not None
            and w11 < len(import_segments)
            and w12 < len(import_segments[w11])
        ):
            v = import_segments[w11][w12]
        elif w10 == 6 and item_index is not None and w11 < len(import_segments[item_index]):
            v = import_segments[item_index][w11]
        elif package is not None:

            def s_cap(w: WorkItem):
                return (
                    w.service.encode()
                    + bytes(w.code_hash)
                    + w.refine_gas_limit.encode()
                    + w.accumulate_gas_limit.encode()
                    + w.export_count.encode()
                    + U16(len(w.import_segments)).encode()
                    + U16(len(w.extrinsic)).encode()
                    + U32(len(w.payload))
                )

            if w10 == 7:
                v = package.encode()
            elif w10 == 8:
                v = package.authorizer.code_hash + package.authorizer.params.encode()
            elif w10 == 9:
                v = package.authorization
            elif w10 == 10:
                v = package.context.encode()
            elif w10 == 11:
                v = Uint(len(package.items)).encode()
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
                v = o[w11].encode()
        elif t is not None:
            if w10 == 16:
                v = t.encode()
            elif w10 == 17 and w11 < len(t):
                v = t[w11].encode()

        if v is None:
            registers[7] = HostStatus.NONE.value
            return CONTINUE, gas, registers, memory, context

        memory_start = int(registers[7])
        f = min(int(registers[8]), len(v))
        l = min(int(registers[9]), len(v) - f)

        if not memory.is_accessible(memory_start, l, Accessibility.WRITE):
            logger.error(
                "Fetch: memory not accessible for write",
                memory_start=memory_start,
                required_size=l,
            )
            raise PvmError(PANIC)

        registers[7] = len(v)
        memory.write(memory_start, v[f : f + l])

        return CONTINUE, gas, registers, memory, context


    @staticmethod
    @INVF.register(2, gas_cost=10)
    def lookup(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        service_data: AccountData,
        service_index: ServiceId,
        accounts: Delta,
    ):
        lookup_key = registers[7]
        hash_addr = registers[8]
        output_addr = registers[9]

        logger.debug(
            "Host call: lookup",
            lookup_key=lookup_key,
            hash_addr=hash_addr,
            output_addr=output_addr,
            service_index=int(service_index),
        )

        a: None | AccountData = None
        if service_index == lookup_key or lookup_key == 2**64 - 1:
            a = service_data
        elif lookup_key in accounts:
            a = accounts[lookup_key]
        
        # Must be able to read the 32-byte hash_addr
        if not memory.is_accessible(hash_addr, 32):
            logger.error(
                "Host call lookup: memory not accessible to read preimage key",
                hash_addr=hash_addr
            )
            raise PvmError(PANIC)

        hash_key = OpaqueHash(memory.read(int(hash_addr), 32))
        if a is not None and a.preimages[hash_key]:
            # Directly get data
            v = a.preimages[hash_key]
            if not v:
                logger.error("Failed key check")
                raise PvmError(PANIC)

            f = min(registers[10], len(v))
            l = min(registers[11], len(v) - f)

            if not memory.is_accessible(output_addr, l, Accessibility.WRITE):
                logger.error(
                    "Host call lookup: memory not accessible for output",
                    output_addr=output_addr,
                    required_size=l,
                )
                raise PvmError(PANIC)

            registers[7] = len(v)
            memory.write(output_addr, v[f:f+l])
            return CONTINUE, gas, registers, memory, context
        else:
            registers[7] = HostStatus.NONE.value
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(3, gas_cost=10)
    def read(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        service_data: AccountData,
        service_index: ServiceId,
        accounts: Delta,
    ):
        service_key = registers[7]
        key_offset = registers[8]
        key_size = registers[9]
        output_offset = registers[10]

        logger.debug(
            "Host call: read",
            service_key=service_key,
            key_offset=key_offset,
            key_size=key_size,
            output_offset=output_offset,
        )

        if service_key == 2**64 - 1:
            service_key = service_index

        a: None | AccountData = None
        if service_key == service_index:
            a = service_data
        elif service_key in accounts:
            a = accounts[service_key]

        key_start, key_len, o = registers[8 : 8 + 3]

        if not memory.is_accessible(key_start, key_len):
            logger.error(
                "Host call read: memory not accessible for key",
                key_offset=key_start,
                key_size=key_len,
            )
            raise PvmError(PANIC)

        value: None | Bytes = None
        key = memory.read(key_start, key_len)

        if a is not None:
            # Directly get data, returns None if not found
            value = a.storage[key]

        if value is None or len(value) == 0:
            registers[7] = HostStatus.NONE.value
        else:
            start = min(int(registers[11]), len(value))
            length = min(int(registers[12]), len(value) - start)

            if not memory.is_accessible(o, length, Accessibility.WRITE):
                logger.error(
                    "Host call read: memory not accessible for output",
                    output_offset=o,
                    required_size=length,
                )
                raise PvmError(PANIC)
            registers[7] = Register(len(value))
            memory.write(o, value[start : start + length])

        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(4, gas_cost=10)
    def write(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        service_data: AccountData,
        service_index: ServiceId,
    ):
        # Get key,value start,end
        [ko, kz, vo, vz] = registers[7 : 7 + 4]

        logger.debug(
            "Host call: write",
            key_offset=ko,
            key_size=kz,
            value_offset=vo,
            value_size=vz,
            service_index=int(service_index),
        )

        if not memory.is_accessible(ko, kz):
            logger.error(
                "Host call write: memory not accessible for key",
                key_offset=ko,
                key_size=kz,
            )
            raise PvmError(PANIC)

    
        # TODO: Handle out of balance using temp caches
        # from jam.state.state import state
        # state.store.save_n_clear_cache()

        k = Bytes(memory.read(ko, kz))
        
        a = service_data.storage

        curr_value = a.get(k)
        storage_len = len(curr_value) if curr_value else HostStatus.NONE.value
        if vz == 0:
            a.__delitem__(k)
        elif memory.is_accessible(vo, vz, Accessibility.WRITE):
            pre_data = a[k]
            a[k] = Bytes(memory.read(vo, vz))
            if service_data.service.t > service_data.service.balance:
                # state.store.clear()
                registers[7] = HostStatus.FULL.value
                if pre_data is None:
                    del a[k]
                else:
                    a[k] = pre_data
                logger.warning("Host call write: storage full", storage_key=k.hex()[:16] + "...")
                return CONTINUE, gas, registers, memory, context
        else:
            logger.error(
                "Host call write: memory not accessible for value",
                value_offset=vo,
                value_size=vz,
            )
            raise PvmError(PANIC)

        registers[7] = storage_len
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(host_call=5, gas_cost=10)
    def info(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        service_index: ServiceId,
        accounts: Delta,
    ):
        target_service = registers[7]
        output_offset = registers[8]

        logger.debug(
            "Host call: info",
            target_service=target_service,
            output_offset=output_offset,
            service_index=int(service_index),
        )

        if target_service == 2**64 - 1:
            target_service = service_index
            
        if target_service not in accounts:
            registers[7] = HostStatus.NONE.value
            return CONTINUE, gas, registers, memory, context

        acc: AccountData = accounts[target_service]
        v = (
            bytes(acc.service.code_hash)
            + U64(acc.service.balance).encode()
            + U64(acc.service.t).encode()
            + U64(acc.service.gas_limit).encode()
            + U64(acc.service.min_gas).encode()
            + U64(acc.service.num_o).encode()
            + U32(acc.service.num_i).encode()
            + U64(acc.service.gratis_offset).encode()
            + U32(acc.service.created_at).encode()
            + U32(acc.service.accumulated_at).encode()
            + U32(acc.service.parent_service).encode()
        )
        f = min(registers[9], len(v))
        l = min(registers[10], len(v) - f)

        if not memory.is_accessible(output_offset, l, Accessibility.WRITE):
            logger.error("Host call info: memory not accessible", output_offset=output_offset, required_size=len(m))
            raise PvmError(PANIC)
        
        registers[7] = len(v)
        memory.write(output_offset, v[f:f+l])

        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(host_call=100, gas_cost=0)
    def log(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: Optional[Any],
        core_index: int,
        service_id: int,
    ):
        message_start = registers[10]
        message_length = registers[11]

        target_start = registers[8]
        target_length = registers[9]

        level = int(registers[7])

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

        log_kwargs = {
            "target": target_str,
            "level": int(level),
            "core_index": core_index,
            "service_id": service_id,
        }

        # Load the default logger
        # jam_logger = logger
        if int(level) == 0:
            jam_logger.error(message_str, **log_kwargs)
        elif int(level) == 1:
            jam_logger.warning(message_str, **log_kwargs)
        elif int(level) == 2:
            jam_logger.info(message_str, **log_kwargs)
        else:
            jam_logger.debug(message_str, **log_kwargs)

        return CONTINUE, gas, registers, memory, context
