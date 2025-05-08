from jam.execution.host_calls._types import accumulation_context,g_dict
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE, PANIC
from jam.types.base.integers.fixed import U32, U64
from jam.types.protocol.core import Gas
from jam.utils.constants import OK, WHO


class accumulateFunctions(INVF):
    @INVF.register(5, gas_cost=10)
    def bless(cls, gas: Gas, registers: Registers, memory: Memory, context: accumulation_context):
        [m,a,v,o,n]=registers[7,7+5]
        if memory.is_accessible(o,12*n):
            # read all n records at once
            buf: bytes = memory.read(o, 12 * n)

            # build a dict mapping each 4-byte U32 → its 8-byte U64
            g_dict: g_dict = {}
            for i in range(0, len(buf), 12):
                chunk = buf[i : i + 12]
                s = U32.decode_from(chunk[:4])             # first  4 bytes
                g = U64.decode_from(chunk[4:12],  offset=0)   # next   8 bytes
                g_dict[s] = g
            if not all(isinstance(x, U32) for x in (m, a, v)):
                return(CONTINUE,WHO,context.x.partial_state.privileges)
            else:
                return(CONTINUE,OK,(m,a,v,g))
        else:
            return(PANIC,registers[7],context.x.partial_state.privileges)
