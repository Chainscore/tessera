from jam.execution.host_calls._types import DeferredTransfer, accumulation_context,service_dict
from jam.execution.host_calls.invocations.accumulate import PsiA, check, fetch_t
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, PANIC, HostStatus
from jam.types.state.delta import AccountData, AccountStorage, LookupTable, LookupTimestamps, PreImageLookup, ServiceCodeHash
from jam.types.base.integers.fixed import U32, U64
from jam.types.protocol.core import BlobLength, Gas, ServiceId
from jam.utils.constants import ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE, CORE_COUNT, MAX_AUTH_QUEUE_ITEMS, TRANSFER_MEMO_SIZE, VALIDATOR_COUNT


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
            if (s.balence<fetch_t(delta[context.x.s_index])):
                return(CONTINUE,HostStatus.CASH,context.x.i_index,delta)
            else:
                return(CONTINUE,check(u=context.x.partial_state,i=(2**28+context.x.i_index-2**8+42)%(2**32-2**9)),delta.append(context.x.i_index,s))
        else:
            return(PANIC,registers[7],context.x.i_index,delta)

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

    @classmethod
    @INVF.register(11, gas_cost=10)
    def transfer(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [d,a,l,o]=registers[7:7+4]
        delta=context.x.partial_state.service_accounts
        if memory.is_accessible(o,TRANSFER_MEMO_SIZE):
            t:DeferredTransfer=DeferredTransfer(sender=context.x.s_index,receiver=d,amount=a,memo=Bytes(memory.read(o,TRANSFER_MEMO_SIZE)),gas=l)
            b=delta[context.x.s_index].balance-a

            if delta[d] is None:
                return(CONTINUE,HostStatus.WHO,context.x.deferred_transfers,delta[context.x.s_index].balence)
            elif l<delta[d].min_gas:
                return(CONTINUE,HostStatus.LOW,context.x.deferred_transfers,delta[context.x.s_index].balence)
            elif b<delta[context.x.s_index]:
                return(CONTINUE,HostStatus.CASH,context.x.deferred_transfers,delta[context.x.s_index].balence)


        else:
            service_acc=delta[context.x.s_index]
            return(PANIC,registers[7],context.x.deferred_transfers,service_acc.balance)
