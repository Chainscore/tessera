from tsrkit_types.bytes import Bytes
from jam.accumulation.types import DeferredTransfer, AccumulationContext, StateContext
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.status import CONTINUE, PANIC, HostStatus, PvmError
from tsrkit_types.sequences import TypedArray
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.protocol.merkle import OptionHash
from jam.types.state.chi import Chi
from jam.types.state.delta import AccountData, AccountStorage, LookupTable, AccountLookup, AccountPreimages, ServiceCodeHash
from tsrkit_types.integers import Uint
from jam.types.protocol.core import BlobLength, Gas, ServiceId, TimeSlot
from jam.utils.constants import ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, CORE_COUNT, MAX_AUTH_QUEUE_ITEMS, PREIMAGE_EVICTION_TIMESLOTS, TRANSFER_MEMO_SIZE, VALIDATOR_COUNT


def check(u:StateContext, i:ServiceId):
    if i not in u.service_accounts:
        return i
    else:
        return check(u, (i-2**8+1) % (2**32-2**9) + 2**8)

class AccumulateFunctions(INVF):

    @classmethod
    @INVF.register(5, gas_cost=10)
    def bless(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [m,a,v,o,n]=registers[7,7+5]
        if not memory.is_accessible(o,12*n):
            raise PvmError(PANIC)
        # read all n records at once
        buf: bytes = memory.read(o, 12 * n)

        # build a dict mapping each 4-byte U32 → its 8-byte U64
        g_dict = {}
        for i in range(0, len(buf), 12):
            chunk = buf[i : i + 12]
            s = Uint[32].decode_from(chunk[:4])             # first  4 bytes
            g = Uint[64].decode_from(chunk[4:12],  offset=0)   # next   8 bytes
            g_dict[s] = g
        if not all(isinstance(x, Uint[32]) for x in (m, a, v)):
            registers[7]=HostStatus.WHO
            return(CONTINUE,registers,memory,context)
        else:
            registers=HostStatus.OK
            context.x.partial_state.privileges=Chi(chi_m=m,chi_a=a,chi_v=v,chi_g=g_dict)
            return(CONTINUE,registers,memory,context)


    @classmethod
    @INVF.register(6, gas_cost=10)
    def assign(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        o=registers[8]
        if not memory.is_accessible(o,32*MAX_AUTH_QUEUE_ITEMS):
            raise PvmError(PANIC)
        buf: bytes=memory.read(o,32*MAX_AUTH_QUEUE_ITEMS)
        c=[]
        for index in range(0, len(buf), 32):
            c.append(bytes(buf[index : index + 32]))

        if registers[7]>=CORE_COUNT:
            registers[7]=HostStatus.CORE
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.OK
            context.x.partial_state.authorizer_keys=c
            return CONTINUE,registers,memory,context



    @classmethod
    @INVF.register(7, gas_cost=10)
    def designate(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        o=registers[7]
        if not memory.is_accessible(o,VALIDATOR_COUNT*336):
            raise PvmError(PANIC)
        buf: bytes=memory.read(o,336*VALIDATOR_COUNT)
        v=[]
        for index in range(0, len(buf), 336):
            v.append(bytes(buf[index : index + 336]))
        registers[7]=HostStatus.OK
        context.x.partial_state.validator_keys=v
        return CONTINUE,registers,memory,context

    @classmethod
    @INVF.register(8, gas_cost=10)
    def checkpoint(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        context.y=context.x
        registers[7]=gas
        return CONTINUE,registers,memory,context

    @classmethod
    @INVF.register(9, gas_cost=10)
    def new(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o,l,g,m]=registers[7:7+4]
        delta=context.x.partial_state.service_accounts
        if not(memory.is_accessible(o,32) and isinstance(l, Uint[32])):
            raise PvmError(PANIC)
        c=memory.read(0,32)
        """
            Creating a new service account initializes empty storage, preimage, and lookup (key = hash(c), len = w8).
            Skips unnecessary a_i/a_o calculations by directly assigning a_t to the new account's balance.
            NOTE: New accounts have a single lookup entry with a value list (hash from memory & length from register).
        """
        a_t=BASIC_MINIMUM_BALANCE+ADDITIONAL_BALANCE_PER_ITEM*2+ADDITIONAL_BALANCE_PER_OCTET*(81+l)
        # AccountData Lookup type needs to be fixed before this func is called
        a=AccountData(code_hash=ServiceCodeHash(c),storage=AccountStorage({}),timestamps=AccountLookup(LookupTable(c,l),[]),lookup=AccountPreimages(),balance=a_t,gas_limit=g,min_gas=m)
        #TODO: Need to re-do it
        s=delta[context.x.s_index]
        """
            NOTE: The use of `.replace()` is necessary here to return a modified copy,
            as per the state transition semantics described in the Gray Paper:
            https://graypaper.fluffylabs.dev/#/9a08063/362c03363103?v=0.6.6
            In case the validation condition fails, the original state must be preserved and returned.
        """

        if (s.balance-a_t<delta[context.x.s_index].t):
            registers[7]=HostStatus.CASH
            return CONTINUE,registers,memory,context
        else:
            x_i=check(u=context.x.partial_state,i=(2**28+(context.x.i_index-2**8+42)%(2**32-2**9)))
            delta[x_i]=a
            s.balance-=a_t
            return CONTINUE,registers,memory,context



    @classmethod
    @INVF.register(10, gas_cost=10)
    def upgrade(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o,g,m]=registers[7:7+3]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        X_s=context.x.partial_state.service_accounts[context.x.s_index]
        X_s.code_hash=memory.read(o,32)
        X_s.gas=g
        X_s.min_gas=m
        registers[7]=HostStatus.OK
        return CONTINUE,registers,memory,context


    # TODO: Need to update the gas with registers[9]
    @classmethod
    @INVF.register(11, gas_cost=10)
    def transfer(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [d,a,l,o]=registers[7:7+4]
        delta=context.x.partial_state.service_accounts
        if not memory.is_accessible(o,TRANSFER_MEMO_SIZE):
            raise PvmError(PANIC)
        t:DeferredTransfer=DeferredTransfer(sender=context.x.s_index,receiver=d,amount=a,memo=Bytes(memory.read(o,TRANSFER_MEMO_SIZE)),gas=l)
        b=delta[context.x.s_index].balance


        if delta[d] is None:
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        elif l<delta[d].min_gas:
            registers[7]=HostStatus.LOW

            return CONTINUE,registers,memory,context
        elif b-a<delta[context.x.s_index]:
            registers[7]=HostStatus.CASH
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.OK
            context.x.deferred_transfers.append(t)
            delta[context.x.s_index].balance-=a
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(12, gas_cost=10)
    def eject(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext, block_timeslot:TimeSlot):
        [d,o]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        accounts=context.x.partial_state.service_accounts

        h=TypedArray[int, 32](memory.read(o,32))
        if d!= context.x.s_index and context.x.partial_state.service_accounts[d] is not None:
            delta=accounts[d]
        else:
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        l=BlobLength(max(81,delta.num_o)-81)
        if delta.code_hash!= context.x.s_index.encode():
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        elif delta.num_i!=2 or delta.timestamps[LookupTable(h,l)] is None:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        elif (
                len(delta.timestamps[LookupTable(h,l)])==2 and
                delta.timestamps[LookupTable(h,l)][1]<block_timeslot-PREIMAGE_EVICTION_TIMESLOTS
        ): # [1] refers to x 2nd timestamp which should be smaller than Block Timeslot - PreImage Eviction Timeslot
            registers[7]=HostStatus.OK
            del context.x.partial_state.service_accounts[d]
            context.x.partial_state.service_accounts[context.x.s_index].balance+=delta.balance
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(13, gas_cost=10)
    def query(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o,l]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        h=TypedArray[int, 32](memory.read(o,32))
        delta=context.x.partial_state.service_accounts[context.x.s_index]
        if delta.timestamps[LookupTable(h,l)] is None:
            registers[7]=HostStatus.NONE
            return CONTINUE,registers,memory,context
        else:
            registers[7]=len(delta.timestamps[LookupTable(h,l)])
            registers[8]=delta.timestamps[LookupTable(h,l)][0] if len(delta.timestamps[LookupTable(h,l)])>=1 else 0
            registers[9]=delta.timestamps[LookupTable(h,l)][1] if len(delta.timestamps[LookupTable(h,l)])>=2 else 0
            registers[10]=delta.timestamps[LookupTable(h,l)][2] if len(delta.timestamps[LookupTable(h,l)])>=3 else 0
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(14, gas_cost=10)
    def solicit(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext,block_timeslot:TimeSlot):
        [o,l]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        h=TypedArray[int, 32](memory.read(o,32))
        delta=context.x.partial_state.service_accounts[context.x.s_index]
        if delta.timestamps[LookupTable(h,l)] is None:
            delta.timestamps[LookupTable(h,l)]=[block_timeslot]
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
        elif len(delta.timestamps[LookupTable(h,l)])==1:
            delta.timestamps[LookupTable(h,l)].append(block_timeslot)
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
        elif len(delta.timestamps[LookupTable(h,l)])==2:
            delta.timestamps[LookupTable(h,l)].append(block_timeslot)
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.FULL
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(15, gas_cost=10)
    def forget(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext,block_timeslot:TimeSlot):
        [o,l]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        h=TypedArray[int, 32](memory.read(o,32))
        delta=context.x.partial_state.service_accounts[context.x.s_index]
        if delta.timestamps[LookupTable(h,l)] is None:
            registers[7]=HostStatus.NONE
            return CONTINUE,registers,memory,context
        else:
            del delta.timestamps[LookupTable(h,l)]
            del delta.preimages[h]
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(16, gas_cost=10)
    def yield_(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext):
        [o,l]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PvmError(PANIC)
        h=TypedArray[int, 32](memory.read(o,32))
        context.x.hash=OptionHash(OpaqueHash(h))
        registers[7]=HostStatus.OK
        return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(27, gas_cost=10)
    def provide(cls, gas: Gas, registers: list, memory: Memory, context: AccumulationContext,service_id:ServiceId):
        [o,l,h_o]=registers[7:7+3]
        if not memory.is_accessible(o,l) and memory.is_accessible(h_o,32):
            raise PvmError(PANIC)
        h=TypedArray[int, 32](memory.read(h_o,32))
        p=Bytes(memory.read(o,l))
        if Hash.blake2b(p)!=h:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        else:
            context.x.partial_state.service_accounts[context.x.s_index].preimages[h]=p
            context.x.preimage.add(h)
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
