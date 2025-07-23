from tsrkit_types import structure, Dictionary, Uint, Bytes, U64, ByteArray

from jam.execution.host_calls.invocations.functions.protocol import (
    InvocationFunctions as INVF,
)
from jam.execution.pvm.program import Program
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.status import (
    PANIC,
    CONTINUE,
    ExecutionStatus,
    HostStatus,
    PvmError,
)
from jam.execution.pvm.types import Accessibility
from jam.types.protocol.core import Gas, Register, ProgramCounter
from jam.execution.pvm.memory import Memory
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
    @INVF.register(17, gas_cost=10)
    def historical_lookup(
        gas: int,
        registers: list,
        memory: Memory,
        context: RefineContext,
        service_id: ServiceId,
        delta: Delta,
        timeslot: TimeSlot,
    ):
        a = None
        if delta[service_id] is not None and registers[7] == 2**64 - 1:
            a = delta[service_id]
        elif delta[registers[7]] is not None:
            a = delta[registers[7]]

        [h, o] = registers[8:10]

        if not memory.is_accessible(h, 32):
            raise PvmError(PANIC)
        elif a is None:
            registers[7] = HostStatus.NONE
            return CONTINUE, registers, memory
        else:
            v = a.historical_lookup(timeslot, Bytes[32](memory.read(h, 32)))

        f = min(int(registers[10]), len(v))
        l = min(int(registers[11]), len(v) - f)

        if not memory.is_accessible(o, l, True):
            raise PvmError(PANIC)

        registers[7] = Register(len(v))
        memory.write(f, v[f:l])
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(19, gas_cost=10)
    def export(
        gas: Gas,
        registers: list,
        memory: Memory,
        context: RefineContext,
        export_segment_offset: int,
    ):
        p = registers[7]
        z = min(registers[8], SEGMENT_SIZE)
        if memory.is_accessible(address=p, length=z, for_write=True):
            from jam.work_package.utils import Utils

            x = Utils.zero_padding(
                value=ByteArray(memory.read(address=p, length=z)), n=Uint(SEGMENT_SIZE)
            )
        else:
            raise PvmError(PANIC)
        if export_segment_offset + len(context.e) >= MAX_EXPORT_ITEM:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        else:
            context.e.append(Segment(x))
            registers[7] = Register(export_segment_offset + len(context.e))
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(20, gas_cost=10)
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
            registers[7] = HostStatus.HUH
            return CONTINUE, gas, registers, context, context

    @staticmethod
    @INVF.register(21, gas_cost=10)
    def peek(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o, s, z] = registers[7:11]
        if not memory.is_accessible(o, z, True):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory
        elif not context.m[n].memory.is_accessible(s, z):
            registers[7] = HostStatus.OOB
            return CONTINUE, gas, registers, memory
        else:
            memory.write(o, context.m[n].memory.read(s, z))
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory

    @staticmethod
    @INVF.register(22, gas_cost=10)
    def poke(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o, s, z] = registers[7:11]

        if not memory.is_accessible(s, z):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory
        elif not context.m[n].memory.is_accessible(o, z, True):
            registers[7] = HostStatus.OOB
            return CONTINUE, gas, registers, memory
        else:
            context.m[n].memory.write(o, memory.read(s, z))
            registers[7] = n
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(23, gas_cost=10)
    def zero(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, p, c] = registers[7:10]
        if n in context.m:
            u = context.m[n].memory
            u.zero_memory_range(p * PVM_MEMORY_PAGE_SIZE, c * PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p, c, Accessibility.WRITE)
        else:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory, context

        if p < 16 or p + c >= 2**32 / PVM_MEMORY_PAGE_SIZE:
            registers[7] = HostStatus.HUH
            return CONTINUE, gas, registers, memory, context
        else:
            context.m[n].memory = u
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(24, gas_cost=10)
    def void(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, p, c] = registers[7:10]
        if n in context.m:
            u = context.m[n].memory
            u.zero_memory_range(p * PVM_MEMORY_PAGE_SIZE, c * PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p, c, Accessibility.NULL)
        else:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory, context

        if (
            p < 16
            or p + c >= 2 * 32 / PVM_MEMORY_PAGE_SIZE
            or not u.is_accessible(p, c)
        ):
            registers[7] = HostStatus.HUH
            return CONTINUE, gas, registers, memory, context
        else:
            context.m[n].memory = u
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(25, gas_cost=10)
    def invoke(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        [n, o] = registers[7, 8]
        if not memory.is_accessible(o, 112, True):
            raise PvmError(PANIC)
        if n not in context.m:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory, context
        m_bytes = memory.read(o, 112)
        # bytes->14size array of 8elements each 0->gas(g) 1-13->register_data(w)
        m_array = [m_bytes[i : i + 8] for i in range(0, len(m_bytes), 8)]
        g, _ = U64.decode_from(bytes(m_array[0]))
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
            registers[7] = U64(
                ExecutionStatus.HOST
            )  # NOTE: Saving the ExecValu on register[7]
            registers[8] = c.value.register
            return CONTINUE, gas, registers, memory, context
        else:
            context.m[n].instruction_counter = i_dash
            if c == ExecutionStatus.PAGE_FAULT:
                registers[7] = U64(ExecutionStatus.PAGE_FAULT)
                registers[8] = c.value.register
                return CONTINUE, registers, memory, context
            elif c == ExecutionStatus.OUT_OF_GAS:
                registers[7] = U64(ExecutionStatus.OUT_OF_GAS)
                return CONTINUE, registers, memory, context
            elif c == ExecutionStatus.PANIC:
                registers[7] = U64(ExecutionStatus.PANIC)
                return CONTINUE, registers, memory, context
            elif c == ExecutionStatus.HALT:
                registers[7] = U64(ExecutionStatus.HALT)
                return CONTINUE, registers, memory, context

    @staticmethod
    @INVF.register(26, gas_cost=10)
    def expunge(gas: Gas, registers: list, memory: Memory, context: RefineContext):
        n = registers[7]
        if n not in context.m:
            return (HostStatus.WHO, context.m)
        else:
            i_c = context.m.instruction_counter
            context.m.pop(n)
            return (i_c, context.m)
