
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
from jam.types.protocol.merkle import OptionHash
from jam.types.state import eta
from jam.types.state.delta import AccountData, PreImageLookup
from jam.execution.host_calls.invocations.functions.accumulate_fns import AccumulateFunctions, check
from jam.execution.pvm.status import ExecutionStatus, PvmError
from jam.utils.constants import MAX_SERVICE_CODE_SIZE

class PsiA(InvocationProtocol):

    def __init__(self, u: StateContext, t:TimeSlot, s:ServiceId, g:Gas, o:OperandTuples):
        self.partial_state = u
        self.timeslot = t
        self.service_id= s
        self.gas= g
        self.operandTuples = o
        self.context = None

    def table(self):
        return {
            0: (GeneralFunctions, ()), # gas (Returns the gas remaining)
            1: (GeneralFunctions, (self.service_id, self.context.x.s_index, self.partial_state.service_accounts)), # lookup
            2: (GeneralFunctions, (self.service_id, self.context.x.s_index, state.delta)), # read
            3: (GeneralFunctions, (self.service_id, self.context.x.s_index)), # write
            4: (GeneralFunctions, (self.context.x.s_index, state.delta)), # info
            5: (AccumulateFunctions, ()), # bless (Updates previlaged accounts)
            6: (AccumulateFunctions, ()), # assign (Updates authorizer_keys/Phi)
            7: (AccumulateFunctions, ()), # designate (Updates validator_keys/Iota)
            8: (AccumulateFunctions, ()), # checkpoint (Special function to update the context[y])
            9: (AccumulateFunctions, ()), # new (Updates the delta with a new service)
            10: (AccumulateFunctions, ()), # upgrade (Updates the service account)
            11: (AccumulateFunctions, ()), # transfer (Updates service deferred transfers & balance)
            12: (AccumulateFunctions, {"block_timeslot": self.timeslot}), # eject (Removal of service account)
            13: (AccumulateFunctions, {}), # query (Updates registers[7,8] wrt lookupTimestamps)
            14: (AccumulateFunctions, {}), # solicit (Updated the lookupTimestamps)
            15: (AccumulateFunctions, {}), # forget (Updates lookupTimestamp & preimage)
            16: (AccumulateFunctions, {}), # yield_ (Updates context[x]_hash)
            18: (GeneralFunctions, {
                "package": None,
                "entropy": state.eta[0],
                "trace": None,
                "item_index": None,
                "import_segments": None,
                "extrinsics": None,
                "o": self.operandTuples,
                "t": None
            }), # fetch (Updates context[x]_hash)
            27: (AccumulateFunctions, {}), # provide (Updates preimage)

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
    def c_function(status:ExecutionStatus | bytes,gas:Gas,context:AccumulationContext)->Tuple[StateContext,DeferredTransfers,OptionHash,Gas,PreimageDict]:
        if status == ExecutionStatus.PANIC or status == ExecutionStatus.OUT_OF_GAS:
            return context.y.partial_state, context.y.deferred_transfers, OptionHash(context.y.hash), gas,context.y.preimage
        elif isinstance(status, bytes):
            return context.x.partial_state, context.x.deferred_transfers, OptionHash(OpaqueHash(status + bytes(32 - len(status)))), gas,context.x.preimage
        else:
            return context.x.partial_state, context.x.deferred_transfers, OptionHash(context.x.hash), gas,context.x.preimage
