from jam.state.accounts import AccountDataView, DeltaView
from jam.state.partial import GhostPartial
from jam.types.state.accumulation.types import (
    AccumulationContext,
    DeferredTransfer,
)
from tsrkit_types import U32, U64, Bytes
from jam.types.protocol.validators import ValidatorData
from jam.log_setup import pvm_logger as logger
from jam.execution.invocations.functions.protocol import (
    InvocationFunctions as INVF,
)
from jam.types.state.iota import Iota
from jam.types.state.phi import AuthorizationQueue, AuthorizerHash
from tsrkit_pvm import (
    Memory,
    CONTINUE,
    PANIC,
    HostStatus,
    PvmError,
    ExecutionStatus,
)
from jam.types import Timestamps
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.protocol.merkle import OptionHash
from jam.types.state.chi import Chi
from jam.types.state.delta import (
    AccountData,
    AccountLookup,
    AccountMetadata,
    AccountPreimages,
    AccountStorage,
    Ai,
    Ao,
    At,
    LookupTable,
    ServiceCodeHash,
)
from jam.types.protocol.core import Balance, BlobLength, Gas, ServiceId, TimeSlot
from jam.utils.constants import (
    ADDITIONAL_BALANCE_PER_ITEM,
    ADDITIONAL_BALANCE_PER_OCTET,
    BASIC_MINIMUM_BALANCE,
    CORE_COUNT,
    MAX_AUTH_QUEUE_ITEMS,
    PREIMAGE_EVICTION_TIMESLOTS,
    TRANSFER_MEMO_SIZE,
    VALIDATOR_COUNT,
)


def check(u: GhostPartial, i: ServiceId):
    if i not in u.service_accounts:
        return i
    else:
        return check(u, ServiceId((i - 2**8 + 1) % (2**32 - 2**9) + 2**8))


class AccumulateFunctions(INVF):
    @staticmethod
    @INVF.register(14, gas_cost=10)
    def bless(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [m, a, v, o, n] = registers[7:7 + 5]

        if not memory.is_accessible(a, 4 * CORE_COUNT):
            logger.warning("Memory access violation in bless function: inaccessible chi_a memory region")
            raise PvmError(PANIC)

        chi_a = U32.decode(memory.read(a, 4 * CORE_COUNT))

        if not memory.is_accessible(o, 12 * n):
            logger.warning("Memory access violation in bless function: inaccessible chi_z memory region")
            raise PvmError(PANIC)

        # Read all n records at once
        buf: bytes = memory.read(o, 12 * n)

        # build a dict mapping each 4-byte U32 → its 8-byte U64
        z_dict = {}
        for i in range(n):
            chunk = buf[12 * i : 12 * i + 12]
            s = U32.decode_from(chunk[:4])  # first  4 bytes
            g = U64.decode_from(chunk[4:12], offset=0)  # next   8 bytes
            z_dict[s] = g

        if context.x.s_index != context.x.partial_state.privileges.chi_m:
            logger.warning("Privilege mismatch in bless function: chi_m does not match s_index")
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        if not all(0 <= x < 2**32 - 1 for x in (m, v)):
            logger.warning(f"Invalid values for m or v in bless function: m={m}, v={v}")
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context

        registers[7] = HostStatus.OK.value
        context.x.partial_state.privileges = Chi(chi_m=m, chi_a=chi_a, chi_v=v, chi_z=z_dict)
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(15, gas_cost=10)
    def assign(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [c, o, a] = registers[7: 7 + 3]

        if not memory.is_accessible(o, 32 * MAX_AUTH_QUEUE_ITEMS):
            logger.warning("Assign: Memory access violation in assign function: inaccessible authorizer_keys memory region")
            raise PvmError(PANIC)

        if c >= CORE_COUNT:
            logger.warning(f"Assign: Invalid value for c={c} in assign function: exceeds CORE_COUNT={CORE_COUNT}")
            registers[7] = HostStatus.CORE.value
            return CONTINUE, gas, registers, memory, context

        if context.x.partial_state.privileges.chi_a[c] != context.x.s_index:
            logger.warning("Assign: Privilege mismatch in assign function: chi_a does not match s_index for given c")
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context

        buf: bytes = memory.read(o, 32 * MAX_AUTH_QUEUE_ITEMS)
        queue = []
        for index in range(MAX_AUTH_QUEUE_ITEMS):
            start = 32 * index
            queue.append(AuthorizerHash(buf[start: start + 32]))

        auth_keys = context.x.partial_state.authorizer_keys
        auth_keys[c] = AuthorizationQueue(queue)
        context.x.partial_state.authorizer_keys = auth_keys

        chi = context.x.partial_state.privileges
        chi.chi_a[c] = ServiceId(a)
        context.x.partial_state.privileges = chi

        registers[7] = HostStatus.OK.value
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(16, gas_cost=10)
    def designate(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        o = registers[7]
        if context.x.s_index != context.x.partial_state.privileges.chi_v:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        if not memory.is_accessible(o, VALIDATOR_COUNT * 336):
            raise PvmError(PANIC)

        buf: bytes = memory.read(o, 336 * VALIDATOR_COUNT)

        context.x.partial_state.validator_keys = Iota([
            ValidatorData.decode(buf[336 * i: 336*i + 336])
            for i in range(VALIDATOR_COUNT)
        ])
        registers[7] = HostStatus.OK.value
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(17, gas_cost=10)
    def checkpoint(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        context.y.i_index = context.x.i_index
        context.y.s_index = context.x.s_index
        context.y.partial_state.store._updates.update(context.x.partial_state.store._updates)
        context.y.deferred_transfers = context.x.deferred_transfers.copy()
        context.y.hash = context.x.hash
        context.y.preimage = context.x.preimage.copy()

        registers[7] = gas
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(18, gas_cost=10)
    def new(gas: Gas, registers: list, memory: Memory, context: AccumulationContext, block_timeslot: TimeSlot):
        [o, l, g, m, f] = registers[7 : 7 + 5]

        if not (memory.is_accessible(o, 32) and l < 2**32 - 1):
            logger.warning("Memory access violation in new function: inaccessible code_hash memory region or invalid length type")
            raise PvmError(PANIC)

        accounts: DeltaView = context.x.partial_state.service_accounts

        if f != 0 and context.x.s_index != context.x.partial_state.privileges.chi_m:
            logger.warning("Privilege mismatch in new function: chi_m does not match s_index when gratis_offset is non-zero")
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context

        c = memory.read(o, 32)
        new_service = AccountData(
            service=AccountMetadata(
                code_hash=ServiceCodeHash(c),
                balance=Balance(BASIC_MINIMUM_BALANCE
                    + ADDITIONAL_BALANCE_PER_ITEM * 2
                    + ADDITIONAL_BALANCE_PER_OCTET * (81+l) - f
                ),
                gas_limit=Gas(g),
                min_gas=Gas(m),
                num_o=Ao(0),
                gratis_offset=Balance(f),
                num_i=Ai(0),
                created_at=TimeSlot(block_timeslot),
                accumulated_at=TimeSlot(0),
                parent_service=ServiceId(context.x.s_index)
            ),
            storage=AccountStorage({}),
            preimages=AccountPreimages({}),
            lookup=AccountLookup({
                LookupTable(hash=ServiceCodeHash(c), length=BlobLength(l)): Timestamps([])
            })
        )

        if accounts[context.x.s_index].service.balance < new_service.service.balance:
            registers[7] = HostStatus.CASH.value
            return CONTINUE, gas, registers, memory, context

        registers[7] = context.x.i_index
        accounts[context.x.i_index] = new_service
        accounts[context.x.s_index].service.balance -= new_service.service.balance
        context.x.i_index = check(
            u=context.x.partial_state,
            i=ServiceId(2**8 + (context.x.i_index - 2**8 + 42) % (2**32 - 2**9)),
        )
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(19, gas_cost=10)
    def upgrade(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o, g, m] = registers[7 : 7 + 3]
        if not memory.is_accessible(o, 32):
            raise PvmError(PANIC)

        xs: AccountDataView = context.x.partial_state.service_accounts[context.x.s_index].service
        xs.code_hash = ServiceCodeHash(memory.read(o, 32))
        xs.gas_limit = Gas(g)
        xs.min_gas = Gas(m)
        registers[7] = HostStatus.OK.value
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(20, gas_cost=10)
    def transfer(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [d, a, l, o] = registers[7 : 7 + 4]
        gas = gas - l

        delta: DeltaView = context.x.partial_state.service_accounts

        if not memory.is_accessible(o, TRANSFER_MEMO_SIZE):
            raise PvmError(PANIC)

        if ServiceId(d) not in delta:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context

        memo = memory.read(o, TRANSFER_MEMO_SIZE)

        t: DeferredTransfer = DeferredTransfer(
            sender=ServiceId(context.x.s_index),
            receiver=ServiceId(d),
            amount=Balance(a),
            memo=Bytes(memo),
            gas=Gas(l),
        )

        new_balance_sender = delta[context.x.s_index].service.balance - Balance(a)

        if l < delta[d].service.min_gas:
            registers[7] = HostStatus.LOW.value
            return CONTINUE, gas, registers, memory, context

        if new_balance_sender < delta[context.x.s_index].service.t:
            registers[7] = HostStatus.CASH.value
            return CONTINUE, gas, registers, memory, context
        else:
            registers[7] = HostStatus.OK.value
            context.x.deferred_transfers.append(t)
            delta[context.x.s_index].service.balance = new_balance_sender
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(21, gas_cost=10)
    def eject(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: AccumulationContext,
        block_timeslot: TimeSlot,
    ):
        [d, o] = registers[7:9]
        if not memory.is_accessible(o, 32):
            raise PvmError(PANIC)

        code_hash = Bytes[32](memory.read(o, 32))

        delta: DeltaView = context.x.partial_state.service_accounts

        account = None
        if d in delta and d != context.x.s_index:
            account = delta[d]

        l = BlobLength(max(81, account.service.num_o) - 81)
        lookup_key = LookupTable(hash=ServiceCodeHash(code_hash), length=BlobLength(l))
        if account == None or account.service.code_hash != ServiceCodeHash(list(context.x.s_index.encode()) + [0] * 28):
            logger.warning("Eject function called with mismatched code hash for service account")
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context
        elif account.service.num_i != 2 or account.lookup[lookup_key] is None:
            logger.warning("Eject function called with invalid number of items or missing lookup entry for service account")
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        elif (
            len(account.lookup[lookup_key]) == 2 and
            account.lookup[lookup_key][1] < block_timeslot - PREIMAGE_EVICTION_TIMESLOTS
        ):  # [1] refers to x 2nd timestamp which should be smaller than Block Timeslot - PreImage Eviction Timeslot
            registers[7] = HostStatus.OK.value
            balance = account.service.balance
            del delta[d].lookup[lookup_key]
            del delta[d].preimages[OpaqueHash(code_hash)]
            del delta[d]
            # TODO: Do we need to remove other storages and preimages associated with this account as well?
            delta[context.x.s_index].service.balance += balance
            return CONTINUE, gas, registers, memory, context
        else:
            logger.warning("Eject function called with invalid lookup entry or timestamp conditions not met for service account")
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(22, gas_cost=10)
    def query(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        preimage_hash_addr, preimage_len = registers[7], registers[8]
        if not memory.is_accessible(preimage_hash_addr, 32):
            raise PvmError(PANIC)

        preimage_hash = Bytes[32](memory.read(preimage_hash_addr, 32))

        lookup_key = LookupTable(hash=preimage_hash, length=BlobLength(preimage_len))
        lookup_value = context.x.partial_state.service_accounts[context.x.s_index].lookup[
            lookup_key
        ] # a' s value
        if lookup_value == None:
            registers[7] = HostStatus.NONE.value
            registers[8] = 0
        elif len(lookup_value) == 0:
            registers[7] = 0
            registers[8] = 0
        elif len(lookup_value) == 1:
            registers[7] = 1 + 2**32 * lookup_value[0]
            registers[8] = 0
        elif len(lookup_value) == 2:
            registers[7] = 2 + 2**32 * lookup_value[0]
            registers[8] = lookup_value[1]
        elif len(lookup_value) == 3:
            registers[7] = 3 + 2**32 * lookup_value[0]
            registers[8] = lookup_value[1] + 2**32 * lookup_value[2]
        else:
            logger.critical(
                "Unexpected metadata",
                service=context.x.s_index,
                lookup=lookup_value,
                lookup_key=lookup_key,
            )
            raise PvmError(PANIC)

        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(23, gas_cost=10)
    def solicit(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: AccumulationContext,
        block_timeslot: TimeSlot,
    ):
        preimage_hash_addr, preimage_len = registers[7], registers[8]

        # Preimage hash
        if not memory.is_accessible(preimage_hash_addr, 32):
            raise PvmError(PANIC)
        preimage_hash = Bytes[32](memory.read(preimage_hash_addr, 32))
        from jam.state.state import state

        # state.store.save_n_clear_cache()

        # Account
        account: AccountData = context.x.partial_state.service_accounts[context.x.s_index]
        lookup_key = LookupTable(hash=preimage_hash, length=BlobLength(preimage_len))
        # storing the initial lookup value
        lookup_val: Timestamps | None = account.lookup[lookup_key]
        # TODO: check updated t > balance
        at = account.service.t

        if not lookup_val:
            account.lookup[lookup_key] = Timestamps([])
            # at = (
            #     at
            #     + (2 * ADDITIONAL_BALANCE_PER_ITEM)
            #     + (preimage_len * ADDITIONAL_BALANCE_PER_OCTET)
            # )
        elif len(lookup_val) == 2:
            lookup_val.append(U32(block_timeslot)) # It should be updating the account data
        else:
            registers[7] = HostStatus.HUH.value
            return ExecutionStatus.CONTINUE, gas, registers, memory, context

        if account.service.balance < account.service.t:
            # state.store.clear()
            registers[7] = HostStatus.FULL.value
            return ExecutionStatus.CONTINUE, gas, registers, memory, context

        # account.lookup[lookup_key] = lookup_val
        registers[7] = HostStatus.OK.value
        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(24, gas_cost=10)
    def forget(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: AccumulationContext,
        block_timeslot: TimeSlot,
    ):
        preimage_hash_addr, preimage_len = registers[7], registers[8]

        if not memory.is_accessible(preimage_hash_addr, 32):
            raise PvmError(PANIC)

        preimage_hash = Bytes[32](memory.read(preimage_hash_addr, 32))
        lookup_key = LookupTable(hash=preimage_hash, length=BlobLength(preimage_len))
        a = context.x.partial_state.service_accounts[context.x.s_index]
        lookup_value = a.lookup[lookup_key]
        if len(a.lookup[lookup_key]) == 1:
            lookup_value.append(block_timeslot)
            a.lookup[lookup_key] = lookup_value
        elif len(a.lookup[lookup_key]) == 0 or (
            len(a.lookup[lookup_key]) == 2 and 
            a.lookup[lookup_key][1] < int(block_timeslot) - PREIMAGE_EVICTION_TIMESLOTS
        ):
            del a.lookup[lookup_key]
            del a.preimages[preimage_hash]
        elif (
            len(a.lookup[lookup_key]) == 3
            and a.lookup[lookup_key][1] < block_timeslot - PREIMAGE_EVICTION_TIMESLOTS
        ):
            lookup_value[0] = lookup_value[2]
            lookup_value[1] = block_timeslot
            lookup_value = lookup_value.pop()
            a.lookup[lookup_key] = lookup_value
        else:
            registers[7] = HostStatus.HUH.value
            return ExecutionStatus.CONTINUE, gas, registers, memory, context
        registers[7] = HostStatus.OK.value
        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(25, gas_cost=10)
    def yield_(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        o = registers[7]

        if not memory.is_accessible(o, 32):
            raise PvmError(PANIC)

        registers[7] = HostStatus.OK.value
        context.x.hash = OptionHash(OpaqueHash(memory.read(o, 32)))
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(26, gas_cost=10)
    def provide(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: AccumulationContext,
        service_id: ServiceId,
    ):
        [o, z] = registers[8: 10]
        d = context.x.partial_state.service_accounts

        s_star = registers[7]
        if registers[7] == 2**64 - 1:
            s_star = service_id

        if not memory.is_accessible(o, z):
            raise PvmError(PANIC)
        i = Bytes(memory.read(o, z))

        if d[s_star] is None:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context
        a = d[s_star]

        lookup = a.lookup[LookupTable(hash=Hash.blake2b(i), length=BlobLength(z))]
        if (lookup is not None and len(lookup) != 0) or (ServiceId(s_star), i) in context.x.preimage:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context

        context.x.preimage.add((s_star, i))
        registers[7] = HostStatus.OK.value
        return CONTINUE, gas, registers, memory, context
