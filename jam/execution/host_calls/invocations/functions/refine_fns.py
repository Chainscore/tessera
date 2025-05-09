from dataclasses import dataclass
from typing import List
from jam.config.settings import Settings,settings
from jam.execution.host_calls._types import integrated_pvm_type, refine_context
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.pvm.program import Program
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.status import HOST, PANIC,CONTINUE, ExecutionStatus
from jam.execution.pvm.types import Accessibility
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.base.integers.general import Int
from jam.types.base.null import Null
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.core import Gas, ProgramCounter
from jam.execution.pvm.register import Registers
from jam.execution.pvm.memory import Memory
from jam.services.historicalLookup import historical_lookup_fn
from jam.types.protocol.core import ServiceId,TimeSlot
from jam.state.components.delta import Delta
from jam.types.base.sequences import ByteArray32
from jam.types.work.item import ImportSpecs
from jam.types.work.package import WorkPackage
from jam.types.work.segment import MultiSegments, Segments,Segment
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.codec.primitives.integers import IntegerCodec
from jam.utils.constants import HUH, MAX_EXPORT_ITEM, NONE, OK, OOB, PVM_MEMORY_PAGE_SIZE, SEGMENT_SIZE, WHO
from jam.types.protocol.crypto import Hash
from jam.utils.json.serde import JsonSerde
from jam.work_package.work_package import WorkPackageProcessing




class refineFunctions(INVF):


    @INVF.register(17, gas_cost=10)
    def historical_lookup(cls, gas: Gas, registers: Registers, memory: Memory, context: refine_context, service_id: ServiceId, delta: Delta, timeslot: TimeSlot):

        if delta[service_id] is not None and registers[7]==2**64-1:
            a=delta[service_id]
        elif delta[registers[7]] is not None:
            a=delta[registers[7]]
        else:
            a=None
        h, o = registers[8:10]

        if not memory.is_accessible(h,32):
            # Not returning right away to return memory(o,l)
            v= False
        elif a==None:
            v= None
        else:
            v=historical_lookup_fn(a,timeslot,ByteArray32(memory.read(h,32)))

        f = min(registers[10], 0 if v is None or v is False else len(v))
        l = min(registers[11], 0-f if v is None or v is False else len(v)-f)

        if v is False or not memory.is_accessible(o, l, True):
            return (PANIC,registers[7],memory.read(o,l))
        elif v is None:
            return (CONTINUE,NONE,memory.read(o,l))
        else:
            return(CONTINUE,len(v),v[f:l])

    @INVF.register(18, gas_cost=10)
    def fetch(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context,work_item_index:int,workpackage:WorkPackage,auth_trace:bytes,imp_segment:MultiSegments):

        db=settings.db
        if registers[10]==0
            v=workpackage.encode()
        elif registers[10]==1:
            v=auth_trace
        elif registers[10]==2 and registers[11]< len(workpackage.items):
            v=workpackage.items[registers[11]].payload

        # TODO: Comparing the context(x (not m,e)) as WI Extrinsics from the db(dummy)
        # https://graypaper.fluffylabs.dev/#/cc517d7/35990035a700?v=0.6.5
        elif registers[10]==3 and registers[11]<len(workpackage.items) and  ItemExtrinsics.compare(work_item_extrinsic=workpackage.items[registers[11]].extrinsic[registers[12]],db=db):
            v=db.get(bytes(workpackage.items[registers[11]].extrinsic[registers[12]].hash))
        elif registers[10]==4 and registers[11]<len(workpackage.items[work_item_index].extrinsic) and ItemExtrinsics.compare(workpackage.items[work_item_index].extrinsic[registers[11]],db=db):
            v=db.get(bytes(workpackage.items[work_item_index].extrinsic[registers[11]].hash))
        elif registers[10]==5 and registers[11]<len(imp_segment) and registers[12]<len(imp_segment[registers[11]]):
            v=imp_segment[registers[11][12]]
        elif registers[10]==6 and registers[11]<len(imp_segment[work_item_index]):
            v=imp_segment[work_item_index][registers[11]]
        elif registers[10]==7:
            v=workpackage.params
        else:
            v=Null

        o=registers
        try:
            length = len(v)
        except (TypeError, AttributeError):
            length = 0
        f = min(registers[8], length)
        l=min(registers[9],length-f)
        if v is not memory.is_accessible(o, l, True):
            return (PANIC,registers[7],memory.read(o,l))
        elif v is False:
            return (CONTINUE,NONE,memory.read(o,l))
        else:
            return (CONTINUE,len(v),v[f:l])

    @INVF.register(19, gas_cost=10)
    def export(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context,export_segment_offset:int):
        p=registers[7]
        z=min(registers[8],SEGMENT_SIZE)
        if memory.is_accessible(p,z,True):
            x=WorkPackageProcessing.zero_padding(value=Bytes(memory.read(p,z)),n=Int(SEGMENT_SIZE))
        else:
            return (PANIC,registers[7],context.m)
        if export_segment_offset+len(context.e)>= MAX_EXPORT_ITEM:
            return (CONTINUE,HUH,context.m)
        else:
            return(CONTINUE,export_segment_offset+len(context.e),context.e.append(Segment(x)))

    @INVF.register(20, gas_cost=10)
    def machine(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [p_o,p_z,i]=registers[7:10]
        if memory.is_accessible(p_o,p_z):
            p=memory.read(p_o,p_z)
        else:
            # p=False
            return (PANIC,registers[7],context.m)


        # Finding the lowest Natural number not existing in the commitment_map iterating from 1 and goes on...
        # 2nd approach by using sorted list...
        # https://graypaper.fluffylabs.dev/#/cc517d7/352e02353a02?v=0.6.5
        n=1
        while n in context.m:
                n += 1

        u=Memory()
        try:
            Program.decode_from(p)
            # TODO: Updating the commitment map, need to see how the dict is appended
            context.m[n]=integrated_pvm_type(program_code=p,memory=u,instruction_counter=i)
            return(CONTINUE,n,context.m)
        except:
            return (CONTINUE,HUH,context.m)

    @INVF.register(21, gas_cost=10)
    def peek(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [n,o,s,z]=registers[7:11]
        if memory.is_accessible(o,z,True):
            return(PANIC,registers[7],memory)
        elif n not in context.m:
            return(CONTINUE,WHO,memory)
        elif not context.m[n].memory.is_accessible(s,z):
            return(CONTINUE,OOB,memory)
        else:
            memory.write(o,context.m[n].memory.read(s,z))
            return(CONTINUE,OK,memory)



    @INVF.register(22, gas_cost=10)
    def poke(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [n,o,s,z]=registers[7:11]

        if memory.is_accessible(s,z):
            return(PANIC,registers[7],context.m)
        elif n not in context.m:
            return(CONTINUE,WHO,context.m)
        elif not context.m[n].memory.is_accessible(o,z,True):
            return(CONTINUE,OOB,context.m)
        else:
            context.m[n].memory.write(o,memory.read(s,z))
            return(CONTINUE,n,context.m)


    @INVF.register(23, gas_cost=10)
    def zero(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [n,p,c]=registers[7:10]
        if n in context.m:
            u=context.m[n].memory
            u.zero_memory_range(p*PVM_MEMORY_PAGE_SIZE,c*PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p,c,Accessibility.write)
        else:
            # u=False
            return (WHO,context.m)

        if p<16 or p+c>= 2**32/PVM_MEMORY_PAGE_SIZE:
            return(HUH,context.m)
        else:
            context.m[n].memory=u
            return(OK,context.m)

    @INVF.register(24, gas_cost=10)
    def void(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [n,p,c]=registers[7:10]
        if n in context.m:
            u=context.m[n].memory
            u.zero_memory_range(p*PVM_MEMORY_PAGE_SIZE,c*PVM_MEMORY_PAGE_SIZE)
            u.alter_accessibility(p,c,Accessibility.null)
        else:
            # u=False
            return (WHO,context.m)

        if p<16 or p+c>= 2*32/PVM_MEMORY_PAGE_SIZE or not u.is_accessible(p,c):
            return(HUH,context.m)
        else:
            context.m[n].memory=u
            return(OK,context.m)

    @INVF.register(25, gas_cost=10)
    def invoke(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        [n,o]=registers[7,8]
        if memory.is_accessible(o,112,True):
            if n not in context.m:
                return(CONTINUE,WHO,registers[8],memory,context.m)
            m_bytes=memory.read(o,112)
            #bytes->14size array of 8elements each 0->gas(g) 1-13->register_data(w)
            m_array = [m_bytes[i:i + 8] for i in range(0, len(m_bytes), 8)]
            g,_=IntegerCodec.decode_from(8,bytes(m_array[0]))
            w=[
                IntegerCodec.decode_from(8, bytes(m_array[i]))[0]
                for i in range(1,14)
            ]
            [c,i_dash,g_dash,w_dash,u_dash]=PVM.execute(context.m[n].program_code,context.m[n].instruction_counter,g,w,context.m[n].memory)
            memory.write(o,g_dash.encode()+w_dash.encode())
            context.m[n].memory=u_dash
            if c==ExecutionStatus.HOST:
                context.m[n].instruction_counter=i_dash+1
                return(CONTINUE,ExecutionStatus.HOST,c.value.register)
            else:
                context.m[n].instruction_counter=i_dash
                if(c==ExecutionStatus.PAGE_FAULT):
                    return(CONTINUE,ExecutionStatus.FAULT,c.value.register,memory,context.m)
                elif(c==ExecutionStatus.OUT_OF_GAS):
                    return(CONTINUE,ExecutionStatus.OUT_OF_GAS,registers[8],memory,context.m)
                elif(c==ExecutionStatus.PANIC):
                    return(CONTINUE,ExecutionStatus.PANIC,registers[8],memory,context.m)
                elif(c==ExecutionStatus.HALT):
                    return(CONTINUE,ExecutionStatus.HALT,registers[8],memory,context.m)

        else:
            return(PANIC,registers[7],registers[8],memory,context.m)


    @INVF.register(26, gas_cost=10)
    def expunge(cls,gas:Gas,registers:Registers,memory:Memory,context:refine_context):
        n=registers[7]
        if n not in context.m:
            return(WHO,context.m)
        else:
            i_c=context.m.instruction_counter
            context.m.pop(n)
            return(i_c,context.m)
