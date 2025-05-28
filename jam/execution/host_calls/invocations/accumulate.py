from typing import Tuple
from jam.accumulation.types import  DeferredTransfers, OperandTuples, AccuContextX,StateContext, AccumulationContext, PreimageDict
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.protocol import InvocationProtocol, DispatchReturn, Context
from jam.types.base import Int, Null
from jam.types.base.integers.fixed import U32
from jam.types.protocol.core import Gas, ProgramCounter, ServiceId, TimeSlot, Register
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.protocol.merkle import OptionHash
from jam.execution.host_calls.invocations.functions.accumulate_fns import AccumulateFunctions, check
from jam.execution.pvm.status import ExecutionStatus
from jam.utils.constants import MAX_SERVICE_CODE_SIZE


class PsiA(InvocationProtocol):

    def __init__(self, u: StateContext, t:TimeSlot, s:ServiceId, g:Gas, o:OperandTuples):
        self.partial_state = u
        self.timeslot = t
        self.service_id = s
        self.gas = g
        self.operandTuples = o
        self.context = AccumulationContext(x=self.initializer_fn(s, u), y=self.initializer_fn(s, u))

    def table(self):
        from jam.state.state import state

        xs = self.context.x.s_index
        delta = self.context.x.partial_state.service_accounts
        return {
            0: (GeneralFunctions, {}),                                                                      # gas (Returns the gas remaining)
            1: (GeneralFunctions, {"service_data": delta[xs], "service_index": xs, "accounts": delta}), # lookup
            2: (GeneralFunctions, {"service_data": delta[xs], "service_index": xs, "accounts": delta}), # read
            3: (GeneralFunctions, {"service_data": delta[xs], "service_index": xs}),                          # write
            4: (GeneralFunctions, {"service_index": xs, "accounts": delta}),                          # info
            5: (AccumulateFunctions, {}),                                                                   # bless (Updates previlaged accounts)
            6: (AccumulateFunctions, {}),                                                                   # assign (Updates authorizer_keys/Phi)
            7: (AccumulateFunctions, {}),                                                                   # designate (Updates validator_keys/Iota)
            8: (AccumulateFunctions, {}),                                                                   # checkpoint (Special function to update the context[y])
            9: (AccumulateFunctions, {}),                                                                   # new (Updates the delta with a new service)
            10: (AccumulateFunctions, {}),                                                                  # upgrade (Updates the service account)
            11: (AccumulateFunctions, {}),                                                                  # transfer (Updates service deferred transfers & balance)
            12: (AccumulateFunctions, {"block_timeslot": self.timeslot}),                                   # eject (Removal of service account)
            13: (AccumulateFunctions, {}),                                                                  # query (Updates registers[7,8] wrt AccountLookup)
            14: (AccumulateFunctions, {}),                                                                  # solicit (Updated the AccountLookup)
            15: (AccumulateFunctions, {}),                                                                  # forget (Updates lookupTimestamp & preimage)
            16: (AccumulateFunctions, {}),                                                                  # yield_ (Updates context[x]_hash)
            18: (GeneralFunctions, {                                                                        # fetch (Updates context[x]_hash)
                "package": None,
                "entropy": state.eta[0],
                "trace": None,
                "item_index": None,
                "import_segments": None,
                "extrinsics": None,
                "o": self.operandTuples,
                "t": None
            }),
            27: (AccumulateFunctions, {}),                                                                 # provide (Updates preimage)
            100: (GeneralFunctions, {}),  # log
        }

    def execute(self):
        meta_n_code = self.partial_state.service_accounts[self.service_id].m_c()
        if meta_n_code is None or len(meta_n_code[1]) > MAX_SERVICE_CODE_SIZE:
            return self.partial_state, DeferredTransfers([]), None, Gas(0), set()

        else:
            gas, status, context = PsiM.execute(
                meta_n_code[1],
                ProgramCounter(5),
                self.gas,
                Int(self.timeslot).encode() + Int(self.service_id).encode() + self.operandTuples.encode(),
                self.dispatch,
                self.context,
            )
            return self.collapse(status, gas, context)

    @staticmethod
    def initializer_fn(s: ServiceId, state_context: StateContext) -> AccuContextX:
        """
        Take Service id and Account to yield a "mutator context" - this is to make sure no changes to actual state are made if we exit
        Args:
            s: Service ID
            state_context: Partial State

        Returns:
            Mutator context
        """
        from jam.state.state import state

        value = (U32.decode_from(bytes(Hash.blake2b(Int(s).encode() + state.eta[0].encode() + Int(state.tau).encode())))[0] % (2**32 - 2**9)) + 2**8
        i = check(state_context, value)
        context = AccuContextX(
            s_index=s,
            partial_state=state_context,
            i_index=i,
            deferred_transfers=DeferredTransfers([]),
            hash=OptionHash(Null),
            preimage=set([]),
        )
        return context

    @staticmethod
    def collapse(
            status: ExecutionStatus | bytes,
            gas: Gas,
            context: AccumulationContext
    ) -> Tuple[StateContext, DeferredTransfers, OptionHash, Gas, PreimageDict]:
        """
        Selects X / Y depending if HALT or PvmErrorc
        Args:
            status: Execution status
            gas: Consumed Gas
            context: X, Y

        Returns:
            StateContext, DeferredTransfers, OptionHash, Gas, PreimageDict
        """
        ctx = context.x
        commitment = ctx.hash

        if status == ExecutionStatus.PANIC or status == ExecutionStatus.OUT_OF_GAS:
            ctx = context.y
            commitment = context.y.hash
        else:
            if isinstance(status, bytes) and len(status) == 32:
                commitment = OptionHash(OpaqueHash(status))

        return ctx.partial_state, ctx.deferred_transfers, commitment, gas, ctx.preimage
