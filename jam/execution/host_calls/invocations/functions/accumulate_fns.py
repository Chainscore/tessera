from jam.execution.host_calls._types import accumulation_context,service_dict
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, PANIC
from jam.types.base.integers.fixed import U32, U64
from jam.types.protocol.core import Gas
from jam.utils.constants import CORE, CORE_COUNT, MAX_AUTH_QUEUE_ITEMS, OK, VALIDATOR_COUNT, WHO


class accumulateFunctions(INVF):
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
                return(CONTINUE,WHO,context.x.partial_state.privileges)
            else:
                return(CONTINUE,OK,(m,a,v,g_dict))
        else:
            return(PANIC,registers[7],context.x.partial_state.privileges)

    @INVF.register(6, gas_cost=10)
    def assign(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        o=registers[8]
        if memory.is_accessible(o,32*MAX_AUTH_QUEUE_ITEMS):
            buf: bytes=memory.read(o,32*MAX_AUTH_QUEUE_ITEMS)
            c=[]
            for index in range(0, len(buf), 32):
                c.append(bytes(buf[index : index + 32]))

            if registers[7]>=CORE_COUNT:
                return(CONTINUE,CORE,context.x.partial_state.q[registers[7]])
            else:
                return(CONTINUE,OK,c)

        else:
            return(PANIC,registers[7],context.x.partial_state.q[registers[7]])

    @INVF.register(7, gas_cost=10)
    def designate(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        o=registers[7]
        if memory.is_accessible(o,VALIDATOR_COUNT*336):
            buf: bytes=memory.read(o,336*VALIDATOR_COUNT)
            v=[]
            for index in range(0, len(buf), 336):
                v.append(bytes(buf[index : index + 336]))
            return(CONTINUE,OK,v)
        else:
            return(PANIC,registers[7],context.x.partial_state.validator_keys)

    # TODO: Return Nothing. Updation path is still on hold
    @INVF.register(8, gas_cost=10)
    def checkpoint(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        context.y=context.x
        registers[7]=gas #gas_dash as per algo


    @INVF.register(9, gas_cost=10)
    def new(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [o,l,g,m]=registers[7,7+4]
        if memory.is_accessible(o,32) and isinstance(l, U32):
            c=memory.read(0,32)

        else:
            return(PANIC,registers[7],context.x.i_index,context.x.partial_state.delta)
