from tsrkit_types.integers import Int
from jam.types.state.accumulation.types import (
    AccumulationContext,
    StateContext,
)
from tsrkit_types import U32, U64, Bytes
from tsrkit_types.sequences import TypedArray
from jam.types.protocol.validators import ValidatorData

from jam.logging import get_logger
from jam.execution.invocations.functions.protocol import (
    InvocationFunctions as INVF,
)
from tsrkit_pvm import (
    Memory,
    CONTINUE,
    PANIC,
    HostStatus,
    PvmError,
    ExecutionStatus,
    Accessibility
)
from jam.types import Timestamps
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.protocol.merkle import OptionHash
from jam.types.state.chi import Chi
from jam.types.state.delta import (
    AccountData,
    AccountStorage,
    LookupTable,
    AccountLookup,
    AccountPreimages,
    ServiceCodeHash,
)
from jam.types.protocol.core import BlobLength, Gas, ServiceId, TimeSlot
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


def check(u: StateContext, i: ServiceId):
    if i not in u.service_accounts:
        return i
    else:
        return check(u, ServiceId((i - 2**8 + 1) % (2**32 - 2**9) + 2**8))

logger = get_logger("host_calls")


class AccumulateFunctions(INVF):
    @staticmethod
    @INVF.register(14, gas_cost=10)
    def bless(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        # TODO: Sync this from 0.6.6 -> 0.6.7
        # 0.6.6: https://graypaper.fluffylabs.dev/#/9a08063/366700366700?v=0.6.6
        # 0.6.7: https://graypaper.fluffylabs.dev/#/7e6ff6a/360e00367600?v=0.6.7
        # change_log: https://github.com/gavofyork/graypaper/pull/393/files#diff-41f3b6a0435c4f16eceda600672b2e6a38411745d9f0277a9bffdf25911d5287

        [m, a, v, o, n] = registers[7:7 + 5]
        if not memory.is_accessible(o, 12 * n):
            raise PvmError(PANIC)
        # read all n records at once
        buf: bytes = memory.read(o, 12 * n)

        # build a dict mapping each 4-byte U32 → its 8-byte U64
        g_dict = {}
        for i in range(0, len(buf), 12):
            chunk = buf[i : i + 12]
            s = U32.decode_from(chunk[:4])  # first  4 bytes
            g = U64.decode_from(chunk[4:12], offset=0)  # next   8 bytes
            g_dict[s] = g
        if not all(isinstance(x, U32) for x in (m, a, v)):
            registers[7] = HostStatus.WHO.value
            return (CONTINUE, gas, registers, memory, context)
        else:
            registers[7] = HostStatus.OK.value
            context.x.partial_state.privileges = Chi(chi_m=m, chi_a=a, chi_v=v, chi_g=g_dict)
            return (CONTINUE, gas, registers, memory, context)

    @staticmethod
    @INVF.register(15, gas_cost=10)
    def assign(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        # TODO: Sync: https://github.com/gavofyork/graypaper/pull/400/files#diff-41f3b6a0435c4f16eceda600672b2e6a38411745d9f0277a9bffdf25911d5287
        o = registers[8]
        if not memory.is_accessible(o, 32 * MAX_AUTH_QUEUE_ITEMS):
            raise PvmError(PANIC)
        buf: bytes = memory.read(o, 32 * MAX_AUTH_QUEUE_ITEMS)
        c = []
        for index in range(0, len(buf), 32):
            c.append(bytes(buf[index : index + 32]))

        if registers[7] >= CORE_COUNT:
            registers[7] = HostStatus.CORE
            return CONTINUE, registers, memory, context
        else:
            context.x.partial_state.authorizer_keys[registers[7]]= c
            registers[7] = HostStatus.OK.value
            return CONTINUE, registers, memory, context

    @staticmethod
    @INVF.register(16, gas_cost=10)
    def designate(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        # TODO: Sync: https://github.com/gavofyork/graypaper/pull/400/files#diff-41f3b6a0435c4f16eceda600672b2e6a38411745d9f0277a9bffdf25911d5287
        o = registers[7]
        if not memory.is_accessible(o, VALIDATOR_COUNT * 336):
            raise PvmError(PANIC)
        buf: bytes = memory.read(o, 336 * VALIDATOR_COUNT)
        # v = []

        # for index in range(0, len(buf), 336):
        #     v.append(bytes(buf[index : index + 336]))
        v = TypedArray([ValidatorData.decode_from(buf[i:i+336]) for i in range(0, len(buf), 336)])

        context.x.partial_state.validator_keys = v
        registers[7] = HostStatus.OK.value
        return CONTINUE, registers, memory, context

    @staticmethod
    @INVF.register(17, gas_cost=10)
    def checkpoint(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        context.y = context.x
        registers[7] = gas
        return CONTINUE, registers, memory, context

    @staticmethod
    @INVF.register(18, gas_cost=10)
    def new(gas: Gas, registers: list, memory: Memory, context: AccumulationContext, slot: TimeSlot):
        # TODO: Sync: https://github.com/gavofyork/graypaper/pull/400/files#diff-41f3b6a0435c4f16eceda600672b2e6a38411745d9f0277a9bffdf25911d5287
        [o, l, g, m] = registers[7 : 7 + 4]
        delta = context.x.partial_state.service_accounts
        if not (memory.is_accessible(o, 32) and isinstance(l, U32)):
            raise PvmError(PANIC)
        c = memory.read(0, 32)
        """
            Creating a new service account initializes empty storage, preimage, and lookup (key = hash(c), len = w8).
            Skips unnecessary a_i/a_o calculations by directly assigning a_t to the new account's balance.
            NOTE: New accounts have a single lookup entry with a value list (hash from memory & length from register).
        """
        # a_t = (
        #     BASIC_MINIMUM_BALANCE
        #     + ADDITIONAL_BALANCE_PER_ITEM * 2
        #     + ADDITIONAL_BALANCE_PER_OCTET * (81 + l)
        # )
        # AccountData Lookup type needs to be fixed before this func is called
        # a = AccountData(
        #     code_hash=ServiceCodeHash(c),
        #     storage=AccountStorage({}),
        #     timestamps=AccountLookup(LookupTable(hash=c,length=l), []),
        #     lookup=AccountPreimages(),
        #     balance=a_t,
        #     gas_limit=g,
        #     min_gas=m,
        # )
        a=AccountData()
        a.service.code_hash=ServiceCodeHash(c)
        a.lookup[LookupTable(hash=Hash.blake2b(c), length=l)] =Timestamps([])
        a.service.gas_limit=g
        a.service.min_gas=m

        # TODO: Need to re-do it
        # s = delta[context.x.s_index]
        s=context.x.partial_state.service_accounts[context.x.s_index]
        """
            NOTE: The use of `.replace()` is necessary here to return a modified copy,
            as per the state transition semantics described in the Gray Paper:
            https://graypaper.fluffylabs.dev/#/9a08063/362c03363103?v=0.6.6
            In case the validation condition fails, the original state must be preserved and returned.
        """

        if s.balance - a.service.t < s.t:
            registers[7] = HostStatus.CASH.value
            return CONTINUE, registers, memory, context
        else:
            x_i = check(
                u=context.x.partial_state,
                i=ServiceId(2**28 + (context.x.i_index - 2**8 + 42) % (2**32 - 2**9)),
            )
            context.x.partial_state.service_accounts[x_i] = a
            s.balance -= a.service.t
            context.x.partial_state.service_accounts[context.x.s_index] = s  # might not require
            return CONTINUE, registers, memory, context

    @staticmethod
    @INVF.register(19, gas_cost=10)
    def upgrade(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o, g, m] = registers[7 : 7 + 3]
        if not memory.is_accessible(o, 32):
            raise PvmError(PANIC)
        X_s = context.x.partial_state.service_accounts[context.x.s_index]
        X_s.service.code_hash = memory.read(o, 32)
        X_s.service.gas = g
        X_s.service.min_gas = m
        registers[7] = HostStatus.OK.value
        return CONTINUE, registers, memory, context

    # TODO: Need to update the gas with registers[9]
    @staticmethod
    @INVF.register(20, gas_cost=10)
    def transfer(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):

        [d, a, l, o] = registers[7 : 7 + 4]
        delta = context.x.partial_state.service_accounts
        if not memory.is_accessible(o, TRANSFER_MEMO_SIZE):
            raise PvmError(PANIC)
        t: DeferredTransfer = DeferredTransfer(
            sender=context.x.s_index,
            receiver=d,
            amount=a,
            memo=Bytes(memory.read(o, TRANSFER_MEMO_SIZE)),
            gas=l,
        )
        b = delta[context.x.s_index].balance

        if delta[d] is None:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, registers, memory, context
        elif l < delta[d].min_gas:
            registers[7] = HostStatus.LOW.value

            return CONTINUE, registers, memory, context
        elif (b - a) < delta[context.x.s_index].service.t:
            registers[7] = HostStatus.CASH.value
            return CONTINUE, registers, memory, context
        else:
            registers[7] = HostStatus.OK.value
            context.x.deferred_transfers.append(t)
            delta[context.x.s_index].balance -= a
            return CONTINUE, registers, memory, context

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
        delta = context.x.partial_state.service_accounts

        h = Bytes[32](memory.read(o, 32))
        if d != context.x.s_index and context.x.partial_state.service_accounts[d] is not None:
            account = delta[d]
        else:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context

        l = BlobLength(max(81, account.service.num_o) - 81)
        if account.service.code_hash != context.x.s_index.encode():
            registers[7] = HostStatus.WHO.value
            return CONTINUE, registers, memory, context
        elif account.service.num_i != 2 or account.lookup[LookupTable( hash = h , length = l )] is None:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        elif (
            len(account.lookup[LookupTable( hash = h , length = l )]) == 2
            and account.lookup[LookupTable( hash = h , length = l )][1] < block_timeslot - PREIMAGE_EVICTION_TIMESLOTS
        ):  # [1] refers to x 2nd timestamp which should be smaller than Block Timeslot - PreImage Eviction Timeslot
            registers[7] = HostStatus.OK.value
            del context.x.partial_state.service_accounts[d]
            context.x.partial_state.service_accounts[context.x.s_index].balance += account.balance
            return CONTINUE, gas, registers, memory, context
        else:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(22, gas_cost=10)
    def query(gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        preimage_hash_addr, preimage_len = registers[7], registers[8]
        if not memory.is_accessible(preimage_hash_addr, 32):
            raise PvmError(PANIC)

        preimage_hash = Bytes[32](memory.read(preimage_hash_addr, 32))

        lookup_key = LookupTable(hash=preimage_hash, length = preimage_len)
        lookup_value = context.x.partial_state.service_accounts[context.x.s_index].lookup[
            lookup_key
        ] # a' s value
        if not lookup_value:
            registers[7] = HostStatus.NONE.value
            registers[8] = 0
        if len(lookup_value) == 0:
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

        state.store.save_n_clear_cache()

        # Account
        account: AccountData = context.x.partial_state.service_accounts[context.x.s_index]
        lookup_key = LookupTable(hash=preimage_hash,length= preimage_len)
        # storing the initial lookup value
        lookup_val: Timestamps | None = account.lookup[lookup_key]
        # Updated t
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
            state.store.clear()
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
        lookup_key = LookupTable( hash = preimage_hash, length = preimage_len)
        a = context.x.partial_state.service_accounts[context.x.s_index]
        lookup_value = a.lookup[lookup_key]
        if len(a.lookup[lookup_key]) == 0 or (
            len(a.lookup[lookup_key]) == 2
            and (a.lookup[lookup_key][1] < int(block_timeslot) - PREIMAGE_EVICTION_TIMESLOTS)
        ):
            del a.lookup[lookup_key]
            del a.preimages[preimage_hash]
        elif len(a.lookup[lookup_key]) == 1:
            lookup_value.append(block_timeslot)
            a.lookup[lookup_key] = lookup_value
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
        context.x.hash = OptionHash(OpaqueHash(memory.read(o, 32)))
        registers[7] = HostStatus.OK.value
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(26, gas_cost=10)
    def provide(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: "AccumulationContext",
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
        if a.lookup[LookupTable(hash = Hash.blake2b(i) , length = z)] != []:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        elif (s_star, i) in context.x.preimage:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        else:
            context.x.preimage.add((s_star, i))
            registers[7] = HostStatus.OK.value
            return CONTINUE, gas, registers, memory, context
