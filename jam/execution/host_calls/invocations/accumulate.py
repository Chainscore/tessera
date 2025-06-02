
from typing import Optional, Tuple
from jam.execution.host_calls._types import  DeferredTransfers, OperandTuples, AccuContextX,StateContext, AccumulationContext, PreimageDict
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.protocol import InvocationProtocol
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.types.base import Int
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.protocol.core import Gas, ProgramCounter, ServiceId, TimeSlot
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.state.state import state
from jam.types.state import eta
from jam.types.state.delta import AccountData, PreImageLookup
from jam.execution.host_calls.invocations.functions.accumulate_fns import AccumulateFunctions, check
from jam.execution.pvm.status import ExecutionStatus, PvmError
from jam.utils.constants import MAX_SERVICE_CODE_SIZE

class PsiA(InvocationProtocol):

    def __init__(self, u: StateContext, t:TimeSlot, s:ServiceId, g:Gas,o:OperandTuples ):
        self.partial_state = u
        self.timeslot = t
        self.service_id= s
        self.gas= g
        self.operandTuples = o
        self.context = None

    def table(self):
        return {
            0: (GeneralFunctions, ()), # gas (Returns the gas remaining)
            1: (GeneralFunctions, (self.service_id,self.context.x.s_index,state.delta)), # lookup
            2: (GeneralFunctions, (self.service_id,self.context.x.s_index,state.delta)), # read
            3: (GeneralFunctions, (self.service_id,self.context.x.s_index)), # write
            4: (GeneralFunctions, (self.context.x.s_index,state.delta)), # info
            5: (AccumulateFunctions, ()), # bless (Updates previlaged accounts)
            6: (AccumulateFunctions, ()), # assign (Updates authorizer_keys/Phi)
            7: (AccumulateFunctions, ()), # designate (Updates validator_keys/Iota)
            8: (AccumulateFunctions, ()), # checkpoint (Special function to update the context[y])
            9: (AccumulateFunctions, ()), # new (Updates the delta with a new service)
            10: (AccumulateFunctions, ()), # upgrade (Updates the service account)
            11: (AccumulateFunctions, ()), # transfer (Updates service deferred transfers & balance)
            12: (AccumulateFunctions, (self.timeslot)), # eject (Removal of service account)
            13: (AccumulateFunctions, ()), # query (Updates registers[7,8] wrt lookupTimestamps)
            14: (AccumulateFunctions, ()), # solicit (Updated the lookupTimestamps)
            15: (AccumulateFunctions, ()), # forget (Updates lookupTimestamp & preimage)
            16: (AccumulateFunctions, ()), # yield_ (Updates context[x]_hash)
            18: (GeneralFunctions, (self.operandTuples,state.eta[0],self.context,OpaqueHash([0] * 32))), # fetch (Updates context[x]_hash)
            27: (AccumulateFunctions, ()), # provide (Updates preimage)

        }

    def execute(self):
        _, c = self.partial_state.service_accounts[self.service_id].m_c()

        if c is None or len(c)>MAX_SERVICE_CODE_SIZE:
            return self.partial_state,DeferredTransfers(),None,Gas(0),PreimageDict({})
        else:
            self.context=AccumulationContext(self.i_function(self.service_id,self.partial_state),self.i_function(self.service_id,self.partial_state))
            gas, status, context=PsiM.execute(
                c,
                ProgramCounter(5),
                self.gas,
                self.timeslot.encode() + self.service_id.encode() + Int(len(self.operandTuples)).encode(),
                self.dispatch,
                self.context,
            )
            print("Execution status", gas, status, context)
            self.partial_state, self.deferred_transfers, hash, self.gas, preimage = self.c_function(status,gas,context)
            return self.partial_state, self.deferred_transfers, hash, self.gas, preimage

    @staticmethod
    def i_function(s: ServiceId,stateContext:StateContext) -> AccuContextX:
        # first = bytes(s.encode())
        # second = bytes(_n_o.encode())
        # third = bytes(timeslot.encode())
        # hashed = ByteArray32(blake2b(first + second + third, digest_size=32).digest())
        # value = ByteArray32.decode_from(hashed)[0]

        # buffer = bytes()
        value = U32.decode_from(
            bytes(Hash.blake2b(s.encode() + state.eta[0].encode() + state.tau.encode()))
        )[0] % (2**32-2**9)+2**8
        i = check(stateContext, value)
        context = AccuContextX(
            s_index=s,
            partial_state=stateContext,
            i_index=i,
            deferred_transfers=DeferredTransfers(),
            hash=None,
            preimage=PreimageDict({}),
        )
        return context


    @staticmethod
    def g_function(status:ExecutionStatus,gas:Gas,registers:Registers,memory:Memory,accountData:AccountData,x:AccuContextX,y:ByteArray32)->Tuple[ExecutionStatus,Gas,Registers,Memory,AccuContextX,ByteArray32]:
        x.partial_state.service_accounts[x.s_index]=accountData
        return status,gas,registers,memory,x,y # returning the updated (x*) component



    @staticmethod
    def c_function(status:ExecutionStatus | bytes,gas:Gas,context:AccumulationContext)->Tuple[StateContext,DeferredTransfers,Optional[bytes],Gas,PreimageDict]:
        if status == ExecutionStatus.PANIC or status == ExecutionStatus.OUT_OF_GAS:
            return context.y.partial_state, context.y.deferred_transfers, context.y.hash, gas,context.y.preimage
        elif isinstance(status, bytes):
            return context.x.partial_state, context.x.deferred_transfers, status, gas,context.x.preimage
        else:
            return context.x.partial_state, context.x.deferred_transfers, context.x.hash, gas,context.x.preimage




#
#
# def c_function(g: Gas,  o: Optional[Bytes] = Status, context: Optional[Tuple[XContent, XContent]] = None) -> (
#         Tuple)[StateContext, DeferredTrasnsfers, Optional[ByteArray32], Gas]:
#     if context is not None:
#         x, y = context
#     else:
#         x, y = None, None
#     print("inside c_function:", g, o, x, y)
#     if o == Status.PANIC or o == Status.OUT_OF_GAS:
#         return y.partial_state, y.deferred_transfers, y.hash, g
#     elif isinstance(o, ByteArray32):
#         return x.partial_state, x.deferred_transfers, o, g
#     else:
#         return x.partial_state, x.deferred_transfers, x.hash, g
#
#
# def g_function(status: Status, gas: Gas, register: Registers, memory: PageMemory, service: AccountData, x: XContent, y: XContent) -> (
#         Tuple)[Status, Gas, Registers, PageMemory, XContent, XContent]:
#     x.partial_state.delta[x.s_index] = service
#     return status, gas, register, memory, x, y
#
#
# class PsiA:
#     header_timeslot = TimeSlot(2)
#     entropy = create_dummy_bytes32()
#     def __init__(self, u: StateContext,
#                  t: TimeSlot, s: ServiceId, g: Gas, o: ):
#         self.partial_state = u
#         self.timeslot = t
#         self.service_id = s
#         self.gas = g
#         self.operands = o
#         self.f_function = self.accumulate_f()
#
#     def process(self):
#         # if self.partial_state.service_accounts[self.service_id].code_hash is None:
#         if self.partial_state.service_accounts.get(self.service_id) is None or self.partial_state.service_accounts.get(self.service_id).code_hash is None:
#             return i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot).partial_state, [], None, 0
#         else:
#             encoded_value = self.timeslot.encode() + self.service_id.encode() + self.operands.encode()
#             return c_function(*PsiM(self.partial_state.service_accounts.get(self.service_id).code_hash, 5, self.gas, encoded_value, self.f_function, (i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot), i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot))).process())
#
#     def accumulate_f(self):
#
#         def read(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
#             return g_function(*HostCall.read(call), x=x, y=y)
#
#         def write(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index)
#             return g_function(*HostCall.write(call), x=x, y=y)
#
#         def lookup(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
#             return g_function(*HostCall.lookup(call), x=x, y=y)
#
#         def gas(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.gas(call)
#
#         def info(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
#             return g_function(*HostCall.info(call), x=x, y=y)
#
#         def bless(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.bless(call)
#
#         def assign(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.assign(call)
#
#         def designate(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.designate(call)
#
#         def checkpoint(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.checkpoint(call)
#
#         def new(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.new(call)
#
#         def upgrade(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.upgrade(call)
#
#         def transfer(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.transfer(call)
#
#         def eject(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.eject(call)
#
#         def query(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall.query(call)
#
#         def solicit(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y, timeslot=self.timeslot)
#             return HostCall.solicit(call)
#
#         def forget(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y, timeslot=self.timeslot)
#             return HostCall.forget(call)
#
#         def _yield(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
#             return HostCall._yield(call)
#
#         def default(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
#             _gas -= 10
#             register[6] = 2 ** 64
#             return Status("continue"), _gas, register
#
#         # Dictionary to map `n` to the corresponding function
#         function_map = {
#             "read": read, 2: read,
#             "write": write, 3: write,
#             "lookup": lookup, 1: lookup,
#             "info": info, 4: info,
#             "bless": bless, 5: bless,
#             "assign": assign, 6: assign,
#             "designate": designate, 7: designate,
#             "gas": gas, 0: gas,
#             "checkpoint": checkpoint, 8: checkpoint,
#             "new": new, 9: new,
#             "upgrade": upgrade, 10: upgrade,
#             "transfer": transfer, 11: transfer,
#             "eject": eject, 12: eject,
#             "query": query, 13: query,
#             "solicit": solicit, 14: solicit,
#             "forget": forget, 15: forget,
#             "yield": _yield, 16: _yield
#         }
#
#         def get_function(n):
#             return function_map.get(n, default)  # Default function if `n` not found
#
#         return get_function  # Return the dynamic function selector
