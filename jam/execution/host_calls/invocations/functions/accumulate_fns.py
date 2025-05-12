import dataclasses
from jam.accumulation.types import StateContext
from jam.execution.host_calls._types import DeferredTransfer, accumulation_context,service_dict
from jam.execution.host_calls.invocations.accumulate import PsiA, check, fetch_t
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm import register
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, PANIC, HostStatus
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.crypto import Hash
from jam.types.state import delta
from jam.types.state.delta import AccountData, AccountStorage, LookupTable, LookupTimestamps, PreImageLookup, ServiceCodeHash
from jam.types.base.integers.fixed import U32, U64
from jam.types.protocol.core import BlobLength, Gas, ServiceId, TimeSlot
from jam.utils.constants import ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, CORE_COUNT, MAX_AUTH_QUEUE_ITEMS, PREIMAGE_EVICTION_TIMESLOTS, TRANSFER_MEMO_SIZE, VALIDATOR_COUNT

def check(u:StateContext,i:ServiceId):
    if u.service_accounts[i] is None:
        return i;
    else:
        return check(u,(i-2**8)%(2**32-2**9)+2**8)

class AccumulateFunctions(INVF):

    @classmethod
    @INVF.register(5, gas_cost=10)
    def bless(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [m,a,v,o,n]=registers[7,7+5]
        if memory.is_accessible(o,12*n):
            # read all n records at once
            buf: bytes = memory.read(o, 12 * n)

            # build a dict mapping each 4-byte U32 → its 8-byte U64
            g_dict: service_dict = {}
            for i in range(0, len(buf), 12):
                chunk = buf[i : i + 12]
                s = U32.decode_from(chunk[:4])             # first  4 bytes
                g = U64.decode_from(chunk[4:12],  offset=0)   # next   8 bytes
                g_dict[s] = g
            if not all(isinstance(x, U32) for x in (m, a, v)):
                return(CONTINUE, HostStatus.WHO,context.x.partial_state.privileges)
            else:
                return(CONTINUE,HostStatus.OK,(m,a,v,g_dict))
        else:
            return(PANIC,registers[7],context.x.partial_state.privileges)

    @classmethod
    @INVF.register(6, gas_cost=10)
    def assign(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        o=registers[8]
        if memory.is_accessible(o,32*MAX_AUTH_QUEUE_ITEMS):
            buf: bytes=memory.read(o,32*MAX_AUTH_QUEUE_ITEMS)
            c=[]
            for index in range(0, len(buf), 32):
                c.append(bytes(buf[index : index + 32]))

            if registers[7]>=CORE_COUNT:
                return(CONTINUE,HostStatus.CORE,context.x.partial_state.q[registers[7]])
            else:
                return(CONTINUE,HostStatus.OK,c)

        else:
            return(PANIC,registers[7],context.x.partial_state.q[registers[7]])

    @classmethod
    @INVF.register(7, gas_cost=10)
    def designate(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        o=registers[7]
        if memory.is_accessible(o,VALIDATOR_COUNT*336):
            buf: bytes=memory.read(o,336*VALIDATOR_COUNT)
            v=[]
            for index in range(0, len(buf), 336):
                v.append(bytes(buf[index : index + 336]))
            return(CONTINUE,HostStatus.OK,v)
        else:
            return(PANIC,registers[7],context.x.partial_state.validator_keys)

    # TODO: Return Nothing. Updation path is still on hold
    @classmethod
    @INVF.register(8, gas_cost=10)
    def checkpoint(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        context.y=context.x
        registers[7]=gas #gas_dash as per algo


    @classmethod
    @INVF.register(9, gas_cost=10)
    def new(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [o,l,g,m]=registers[7:7+4]
        delta=context.x.partial_state.service_accounts
        if memory.is_accessible(o,32) and isinstance(l, U32):
            c=memory.read(0,32)
            """
            creating a new service account results to empty storage/preimage nad lookup with hash(c) and length(l from w8)
            Not Doing unwanted calc of a_i/a_o finding the direct value of a_t for assigning it to the balence for the newly created service_acc
            NOTE: While creating a new service_acc it will have a single lookup(key with a value[])
            """
            a_t=BASIC_MINIMUM_BALANCE+ADDITIONAL_BALANCE_PER_ITEM*2+ADDITIONAL_BALANCE_PER_OCTET*(81+l)
            # AccountData Lookup type needs to be fixed before this func is called
            a=AccountData(code_hash=ServiceCodeHash(c),storage=AccountStorage(),timestamps=LookupTimestamps(LookupTable(hash=ServiceCodeHash(c),length=BlobLength(l)),[]),lookup=PreImageLookup(),balance=a_t,gas_limit=g,min_gas=m)
            #TODO: Need to re-do it
            s=delta[context.x.s_index]
            s.balance=s.balance-a_t
            if (s.balence<delta[context.x.s_index].t): #NOTE: Delta.t to calculate the t of the account
                registers[7]=HostStatus.CASH
                return CONTINUE,registers,memory,context
            else:
                x_i=check(u=context.x.partial_state,i=(2**28+(context.x.i_index-2**8+42)%(2**32-2**9)))
                delta[x_i]=a
                # context.x.
                return CONTINUE,registers,memory,context
        else:
            raise PANIC

    @classmethod
    @INVF.register(10, gas_cost=10)
    def upgrade(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [o,g,m]=registers[7:7+3]
        if memory.is_accessible(o,32):
            c=memory.read(o,32)
            return(CONTINUE,HostStatus.OK,c,g,m)
        else:
            X_s=context.x.partial_state.service_accounts[context.x.s_index]
            return(PANIC,registers[7],X_s.code_hash,X_s.gas,X_s.min_gas)

    # TODO: Need to update the gas with registers[9]
    @classmethod
    @INVF.register(11, gas_cost=10)
    def transfer(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [d,a,l,o]=registers[7:7+4]
        delta=context.x.partial_state.service_accounts
        if memory.is_accessible(o,TRANSFER_MEMO_SIZE):
            t:DeferredTransfer=DeferredTransfer(sender=context.x.s_index,receiver=d,amount=a,memo=Bytes(memory.read(o,TRANSFER_MEMO_SIZE)),gas=l)
            b=delta[context.x.s_index].balance-a

            if delta[d] is None:
                registers[7]=HostStatus.WHO
                return CONTINUE,registers,memory,context
            elif l<delta[d].min_gas:
                registers[7]=HostStatus.LOW

                return CONTINUE,registers,memory,context
            elif b<delta[context.x.s_index]:
                registers[7]=HostStatus.CASH
                return CONTINUE,registers,memory,context
            else:
                registers[7]=HostStatus.OK
                context.x.deferred_transfers.append(t)
                delta[context.x.s_index].balance=b
                return CONTINUE,registers,memory,context

        else:
            raise PANIC

    @classmethod
    @INVF.register(12, gas_cost=10)
    def eject(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context,block_timeslot:TimeSlot):
        [d,o]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PANIC
        accounts=context.x.partial_state.service_accounts

        h=memory.read(o,32)
        if d!= context.x.s_index and context.x.partial_state.service_accounts[d] is not None:
            delta=accounts[d]
        else:
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        l=max(81,delta.num_o)-81
        s_dash=accounts[context.x.s_index] #NOTE: Might need to change as per we need the delta not be altered always
        s_dash.balance+=delta.balance

        if delta.code_hash!= context.x.s_index.encode():
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        elif delta.num_i!=2 or delta.timestamps[h,l] is None:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        elif len(delta.timestamps[h,l])==2 and delta.timestamps[h,l][1]<block_timeslot-PREIMAGE_EVICTION_TIMESLOTS # [1] refers to x 2nd timestamp which should be smaller than Block Timeslot - PreImage Eviction Timeslot
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context

    @classmethod
    @INVF.register(13, gas_cost=10)
    def query(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [o,z]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PANIC
        h=memory.read(o,32)
        if not context.x.partial_state.service_accounts[context.x.s_index].timestamps[h,z]:
            registers[7]=HostStatus.NONE
            return CONTINUE,registers,memory,context
        a=context.x.partial_state.service_accounts[context.x.s_index].timestamps[h,z]
        if len(a)==0:
            registers[7]=0
            registers[8]=0
            return CONTINUE,registers,memory,context
        elif len(a)==1:
            registers[7]=1+2**32*a[0]
            registers[8]=0
            return CONTINUE,registers,memory,context
        elif len(a)==2:
            registers[7]=2+2**32*a[0]
            registers[8]=a[1]
            return CONTINUE,registers,memory,context
        elif len(a)==3:
            registers[7]=3+2**32*a[0]
            registers[8]=a[1]+2**32*a[2]
            return CONTINUE,registers,memory,context


    @classmethod
    @INVF.register(14, gas_cost=10)
    def solicit(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context,block_timeslot:TimeSlot):
        [o,z]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PANIC
        h=memory.read(o,32)
        new_context = dataclasses.replace(context) # coping context to preserve the initial one
        a = new_context.x.partial_state.service_accounts[new_context.x.s_index]
        if a.timestamps[h,z] is None:
            a.timestamps[h,z]=[]

        elif len(a.timestamps[h,z])==2:
            a.timestamps[h,z].append(block_timeslot)
        else:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context

        if a.balance<a.t:
            registers[7]=HostStatus.FULL
            return CONTINUE,registers,memory,context
        else:
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,new_context #returning the updated context

    @classmethod
    @INVF.register(15, gas_cost=10)
    def forget(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context,block_timeslot:TimeSlot):
        [o,z]=registers[7,8]
        if not memory.is_accessible(o,32):
            raise PANIC
        h=memory.read(o,32)
        new_context = dataclasses.replace(context) # coping context to preserve the initial one
        a = new_context.x.partial_state.service_accounts[new_context.x.s_index]
        if len(a.timestamps[h,z])==0 or (len(a.timestamps[h,z])==2 and (a.timestamps[h,z][1]<block_timeslot-PREIMAGE_EVICTION_TIMESLOTS)):
            del a.timestamps[h,z]
            del a.lookup[h]
        elif len(a.timestamps[h,z])==1:
            a.timestamps[h,z].append(block_timeslot)
        elif len(a.timestamps[h,z])==3 and a.timestamps[h,z][1]<block_timeslot-PREIMAGE_EVICTION_TIMESLOTS:
            a.timestamps[h,z][0]=a.timestamps[h,z][2]
            a.timestamps[h,z][1]=block_timeslot
            a.timeslot[h,z].pop()
        else:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        registers[7]=HostStatus.OK
        return CONTINUE,registers,memory,context

    @classmethod
    @INVF.register(16, gas_cost=10)
    def yield_(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        o=registers[7]
        if not memory.is_accessible(o,32):
            raise PANIC
        context.y=ByteArray32(memory.read(o,32))
        registers[7]=HostStatus.OK
        return CONTINUE,registers,memory,context

    @classmethod
    @INVF.register(27, gas_cost=10)
    def provide(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context,service_id:ServiceId):
        [o,z]=registers[8,9]
        d=context.x.partial_state.service_accounts
        s_star=registers[7]
        if registers[7]==2**64-1:
            s_star=service_id
        if not memory.is_accessible(o,z):
            raise PANIC
        i=memory.read(o,z)
        if d[s_star] is None:
            registers[7]=HostStatus.WHO
            return CONTINUE,registers,memory,context
        a=d[s_star]
        if a.timestamps[Hash.blake2b(i),z]!=[]:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        elif context.x.preimage[s_star]==i:
            registers[7]=HostStatus.HUH
            return CONTINUE,registers,memory,context
        else:
            context.x.preimage=i
            registers[7]=HostStatus.OK
            return CONTINUE,registers,memory,context
