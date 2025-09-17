from tsrkit_types import structure, Dictionary, Uint, Bytes, U64, ByteArray

from jam.execution.invocations.functions.protocol import (
    InvocationFunctions as INVF,
)

import os

# Pre-compute PVM mode imports to avoid dynamic imports during execution
_PVM_MODE = os.environ.get("PVM_MODE", "interpreter")
if _PVM_MODE == "recompiler":
    from tsrkit_pvm import REC_Memory as Memory, REC_Program as Program, Recompiler as PVM
else:
    from tsrkit_pvm import INT_Memory as Memory, INT_Program as Program, Interpreter as PVM


from tsrkit_pvm import (
    Accessibility,
    PANIC,
    CONTINUE,
    ExecutionStatus,
    HostStatus,
    PvmError,
)
from jam.types.protocol.core import Gas, Register, ProgramCounter
from jam.types.protocol.core import ServiceId, TimeSlot
from jam.types.state.delta import Delta
from jam.types.work import Segment, Segments
from jam.utils.constants import MAX_EXPORT_ITEM, PVM_MEMORY_PAGE_SIZE, SEGMENT_SIZE


@structure
class IntegratedPVM:
    program_code: bytes
    memory: Memory
    instruction_counter: ProgramCounter


class RefinementMap(Dictionary[Uint, IntegratedPVM]):
    """Integrated PVM Dict(m)"""


@structure
class RefineContext:
    m: RefinementMap
    e: Segments


class RefineFunctions(INVF):
    @staticmethod
    @INVF.register(6, gas_cost=10)
    def historical_lookup(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: RefineContext,
        service_id: ServiceId,
        delta: Delta,
        timeslot: TimeSlot,
    ):
        # Select account: if w7 == 2^64-1 use the explicit `service_id` arg, else w7 holds the sid
        a = None
        if delta[service_id] is not None and registers[7] == 2**64 - 1:
            a = delta[service_id]
        elif delta[registers[7]] is not None:
            a = delta[registers[7]]

        h, o = registers[8], registers[9]  # h: ptr to 32-byte hash, o: output ptr (0 = probe)

        # Must be able to read the 32-byte hash
        if not memory.is_accessible(h, 32):
            raise PvmError(PANIC)

        # No such account → signal “none” as the u64 sentinel (not an enum object!)
        if a is None:
            registers[7] = HostStatus.NONE.value
            return CONTINUE, gas, registers, memory, context

        # Lookup preimage
        preimage = a.historical_lookup(timeslot, Bytes[32](memory.read(h, 32)))
        if preimage is None:
            registers[7] = 2**64 - 1
            return CONTINUE, gas, registers, memory, context

        v = bytes(preimage)

        # Off/len: req==0 means "rest of blob"
        f = min(int(registers[10]), len(v))
        req = int(registers[11])
        l = min(req if req != 0 else len(v), max(0, len(v) - f))

        # Two-phase contract: if o==0, it's a size probe — don't write, just return total length.
        if o != 0 and l > 0:
            if not memory.is_accessible(o, l, True):
                raise PvmError(PANIC)
            memory.write(o, v[f:f + l])

        # w7 returns the FULL preimage length, not the number written
        registers[7] = len(v)
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(7, gas_cost=10)
    def export(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: RefineContext,
        export_segment_offset: int,
    ):
        p = registers[7]
        z = min(registers[8], SEGMENT_SIZE)
        if memory.is_accessible(address=p, length=z, for_write=True): #TODO: need to change to readable only
            from jam.incore.utils import Utils
            x = Utils.zero_padding(
                value=ByteArray(memory.read(address=p, length=z)), n=SEGMENT_SIZE
            )
        else:
            raise PvmError(PANIC)
        if export_segment_offset + len(context.e) >= MAX_EXPORT_ITEM:
            registers[7] = HostStatus.FULL.value
            return CONTINUE, gas, registers, memory, context
        else:
            context.e.append(Segment(x))
            registers[7] = Register(export_segment_offset + len(context.e))
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(8, gas_cost=10)
    def machine(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [p_o, p_z, i] = registers[7:10]
        if memory.is_accessible(p_o, p_z):
            p = memory.read(p_o, p_z)
        else:
            raise PvmError(PANIC)
        # Finding the lowest Natural number not existing in the commitment_map iterating from 1 and goes on...
        # 2nd approach by using sorted list...
        # https://graypaper.fluffylabs.dev/#/cc517d7/352e02353a02?v=0.6.5
        n = 1
        while n in context.m:
            n += 1

        u = Memory()
        try:
            Program.decode_from(p)
            # TODO: Updating the commitment map, need to see how the dict is appended
            context.m[n] = IntegratedPVM(
                program_code=p, memory=u, instruction_counter=i
            )
            registers[7] = n
            return CONTINUE, gas, registers, memory, context
        except:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, context, context

    @staticmethod
    @INVF.register(9, gas_cost=10)
    def peek(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o, s, z] = registers[7:11]
        if not memory.is_accessible(o, z, True):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory,context
        elif not context.m[n].memory.is_accessible(s, z):
            registers[7] = HostStatus.OOB.value
            return CONTINUE, gas, registers, memory,context
        else:
            memory.write(o, context.m[n].memory.read(s, z))
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory,context

    @staticmethod
    @INVF.register(10, gas_cost=10)
    def poke(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o, s, z] = registers[7:11]

        if not memory.is_accessible(s, z):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory,context
        elif not context.m[n].memory.is_accessible(o, z, True):
            registers[7] = HostStatus.OOB.value
            return CONTINUE, gas, registers, memory,context
        else:
            context.m[n].memory.write(o, memory.read(s, z))
            registers[7] = n
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(11, gas_cost=10)
    def pages(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, start_p, num_p, r] = registers[7:11]
        if n in context.m:
            u = context.m[n].memory
            if( 
                start_p < 16 or 
                start_p + num_p >= 2 * 32 / PVM_MEMORY_PAGE_SIZE or 
                (not u.is_accessible(start_p, num_p, Accessibility.NULL) and r > 2)
                ):
                registers[7] = HostStatus.HUH.value
                return CONTINUE, gas, registers, memory, context
            else:
                # Zero
                if r < 3:
                    u.zero_memory_range(start_p, num_p)

                # Void
                if r == 0:
                    u.alter_accessibility(start_p, num_p, Accessibility.NULL)
                elif r == 1 or r == 3:
                    u.alter_accessibility(start_p, num_p, Accessibility.READ)
                elif r == 2 or r == 4:
                    u.alter_accessibility(start_p, num_p, Accessibility.WRITE)

                context.m[n].memory = u
                registers[7] = HostStatus.OK.value
                return CONTINUE, gas, registers, memory, context
        else:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(12, gas_cost=10)
    def invoke(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o] = registers[7:9]
        if not memory.is_accessible(o, 112, True):
            raise PvmError(PANIC)
        if n not in context.m:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context
        m_bytes = memory.read(o, 112)
        # bytes->14size array of 8elements each 0->gas(g) 1-13->register_data(w)
        m_array = [m_bytes[i : i + 8] for i in range(0, len(m_bytes), 8)]
        g, _ = U64.decode_from(bytes(m_array[0]))
        # TODO: Concat fix: https://github.com/gavofyork/graypaper/pull/438/files#diff-41f3b6a0435c4f16eceda600672b2e6a38411745d9f0277a9bffdf25911d5287
        w = [U64.decode_from(bytes(m_array[i]))[0] for i in range(1, 14)]
        [c, i_dash, g_dash, w_dash, u_dash] = PVM.execute(
            context.m[n].program_code,
            context.m[n].instruction_counter,
            g,
            w,
            context.m[n].memory,
        )
        memory.write(o, g_dash.encode() + w_dash.encode())
        context.m[n].memory = u_dash
        if c == ExecutionStatus.HOST:
            context.m[n].instruction_counter = i_dash + 1
            registers[7] = U64(ExecutionStatus.HOST)  # NOTE: Saving the ExecValu on register[7]
            registers[8] = c.value.register
            return CONTINUE, gas, registers, memory, context
        else:
            context.m[n].instruction_counter = i_dash
            if c == ExecutionStatus.PAGE_FAULT:
                registers[7] = U64(ExecutionStatus.PAGE_FAULT)
                registers[8] = c.value.register
                return CONTINUE, gas, registers, memory, context
            elif c == ExecutionStatus.OUT_OF_GAS:
                registers[7] = U64(ExecutionStatus.OUT_OF_GAS)
                return CONTINUE, gas, registers, memory, context
            elif c == ExecutionStatus.PANIC:
                registers[7] = U64(ExecutionStatus.PANIC)
                return CONTINUE, gas, registers, memory, context
            elif c == ExecutionStatus.HALT:
                registers[7] = U64(ExecutionStatus.HALT)
                return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(13, gas_cost=10)
    def expunge(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        n = registers[7]
        if n not in context.m:
            registers[7] = HostStatus.WHO.value
            return CONTINUE, gas, registers, memory, context
        else:
            context.m.pop(n)
            registers[7] = n
            return CONTINUE, gas, registers, memory, context
