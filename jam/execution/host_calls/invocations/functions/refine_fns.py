from dataclasses import dataclass

from tsrkit_types import ByteArray

from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.program import Program
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.status import PANIC, CONTINUE, ExecutionStatus, HostStatus, PvmError
from jam.execution.pvm.types import Accessibility
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.integers import Uint
from tsrkit_types.bytes import Bytes
from jam.types.protocol.core import Gas, Register, ProgramCounter
from jam.execution.pvm.memory import Memory
from jam.types.protocol.core import ServiceId,TimeSlot
from jam.types.state.delta import Delta
from tsrkit_types.sequences import TypedArray
from jam.types.work import Segment, Segments
from tsrkit_types.struct import structure
from jam.utils.constants import  MAX_EXPORT_ITEM, PVM_MEMORY_PAGE_SIZE, SEGMENT_SIZE
from jam.work_package.work_package import WorkPackageProcessing

@structure
class IntegratedPVM:
    program_code: bytes
    memory: Memory
    instruction_counter: ProgramCounter

RefinementMap = Dictionary[int, IntegratedPVM]

@structure
class RefineContext:
    m: RefinementMap
    e: Segments

class RefineFunctions(INVF):

    @staticmethod
    @INVF.register(17, gas_cost=10)
    def historical_lookup(gas: int, registers: list, memory: Memory, context: RefineContext, service_id: ServiceId, delta: Delta, timeslot: TimeSlot):

        a = None
        if delta[service_id] is not None and registers[7]==2**64-1:
            a=delta[service_id]
        elif delta[registers[7]] is not None:
            a=delta[registers[7]]

        [h, o] = registers[8:10]

        if not memory.is_accessible(h,32):
            raise PvmError(PANIC)
        elif a is None:
            registers[7] = HostStatus.NONE
            return CONTINUE, registers, memory
        else:
            v = a.historical_lookup(timeslot, TypedArray[int, 32](memory.read(h,32)))

        f = min(int(registers[10]), len(v))
        l = min(int(registers[11]), len(v)-f)

        if not memory.is_accessible(o, l, True):
            raise PvmError(PANIC)

        registers[7] = Register(len(v))
        memory.write(f, v[f:l])
        return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(19, gas_cost=10)
    def export(gas: Gas, registers: list, memory: Memory, context: RefineContext, export_segment_offset:int):
        p = registers[7]
        z = min(registers[8], SEGMENT_SIZE)
        if memory.is_accessible(address=p, length=z, for_write=True):
            x = WorkPackageProcessing.zero_padding(value=ByteArray(memory.read(address=p,length=z)), n=Uint(SEGMENT_SIZE))
        else:
            raise PvmError(PANIC)
        if export_segment_offset + len(context.e) >= MAX_EXPORT_ITEM:
            registers[7] = HostStatus.HUH.value
            return CONTINUE, gas, registers, memory, context
        else:
            context.e.append(Segment(x))
            registers[7] = Register(export_segment_offset+len(context.e))
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(20, gas_cost=10)
    def machine(gas:Gas,registers:list,memory:Memory,context:RefineContext):
        [p_o,p_z,i] = registers[7:10]
        if memory.is_accessible(p_o,p_z):
            p=memory.read(p_o,p_z)
        else:
            raise PvmError(PANIC)
        # Finding the lowest Natural number not existing in the commitment_map iterating from 1 and goes on...
        # 2nd approach by using sorted list...
        # https://graypaper.fluffylabs.dev/#/cc517d7/352e02353a02?v=0.6.5
        n=1
        while n in context.m:
                n += 1

        u = Memory()
        try:
            Program.decode_from(p)
            # TODO: Updating the commitment map, need to see how the dict is appended
            context.m[n] = IntegratedPVM(program_code=p,memory=u,instruction_counter=i)
            registers[7] = n
            return CONTINUE ,gas ,registers ,memory, context
        except:
            registers[7]=HostStatus.HUH
            return CONTINUE ,gas ,registers ,context ,context

    @staticmethod
    @INVF.register(21, gas_cost=10)
    def peek(gas:Gas, registers:list, memory:Memory, context:RefineContext):
        [n,o,s,z] = registers[7:11]
        if not memory.is_accessible(o,z,True):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers,memory
        elif not context.m[n].memory.is_accessible(s,z):
            registers[7] = HostStatus.OOB
            return CONTINUE, gas, registers, memory
        else:
            memory.write(o,context.m[n].memory.read(s,z))
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory


    @staticmethod
    @INVF.register(22, gas_cost=10)
    def poke(gas:Gas, registers:list, memory:Memory, context:RefineContext):
        [n,o,s,z] = registers[7:11]

        if not memory.is_accessible(s,z):
            raise PvmError(PANIC)
        elif n not in context.m:
            registers[7]=HostStatus.WHO
            return CONTINUE, gas, registers ,memory
        elif not context.m[n].memory.is_accessible(o,z,True):
            registers[7]=HostStatus.OOB
            return CONTINUE, gas, registers ,memory
        else:
            context.m[n].memory.write(o,memory.read(s,z))
            registers[7] = n
            return CONTINUE, gas, registers,memory,context


    @staticmethod
    @INVF.register(23, gas_cost=10)
    def zero(gas:Gas, registers:list, memory:Memory, context:RefineContext):
        [n,p,c] = registers[7:10]
        if n in context.m:
            u = context.m[n].memory
            u.zero_memory_range(p*PVM_MEMORY_PAGE_SIZE,c*PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p,c,Accessibility.WRITE)
        else:
            registers[7] = HostStatus.WHO
            return CONTINUE, gas, registers, memory, context

        if p<16 or p+c>= 2**32/PVM_MEMORY_PAGE_SIZE:
            registers[7] = HostStatus.HUH
            return CONTINUE, gas ,registers, memory, context
        else:
            context.m[n].memory=u
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(24, gas_cost=10)
    def void(gas:Gas,registers: list, memory:Memory, context:RefineContext):
        [n,p,c]=registers[7:10]
        if n in context.m:
            u=context.m[n].memory
            u.zero_memory_range(p*PVM_MEMORY_PAGE_SIZE,c*PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p,c,Accessibility.NULL)
        else:
            registers[7]=HostStatus.WHO
            return CONTINUE, gas, registers, memory, context

        if p<16 or p+c>= 2*32/PVM_MEMORY_PAGE_SIZE or not u.is_accessible(p,c):
            registers[7]=HostStatus.HUH
            return CONTINUE, gas, registers, memory, context
        else:
            context.m[n].memory=u
            registers[7]=HostStatus.OK
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(25, gas_cost=10)
    def invoke(gas:Gas,registers:list,memory:Memory,context:RefineContext):
        [n,o]=registers[7,8]
        if not memory.is_accessible(o,112,True):
            raise PvmError(PANIC)
        if n not in context.m:
            registers[7]=HostStatus.WHO
            return CONTINUE, gas, registers, memory, context
        else:
            # Invoke the PVM
            status, pc, remaining_gas, registers_out, memory_out = PVM.execute(
                context.m[n].program_code,
                context.m[n].instruction_counter,
                gas,
                registers,
                context.m[n].memory
            )
            # Update the context
            context.m[n].instruction_counter = pc
            context.m[n].memory = memory_out
            # Write the registers to memory
            for i, reg in enumerate(registers_out):
                memory.write(o + i * 8, Uint[64](reg).encode())
            registers[7] = HostStatus.OK
            return CONTINUE, gas, registers, memory, context

    @staticmethod
    @INVF.register(26, gas_cost=10)
    def expunge(gas:Gas,registers:list,memory:Memory,context:RefineContext):
        n=registers[7]
        if n not in context.m:
            registers[7]=HostStatus.WHO
            return CONTINUE, gas, registers, memory, context
        else:
            del context.m[n]
            registers[7]=HostStatus.OK
            return CONTINUE, gas, registers, memory, context
