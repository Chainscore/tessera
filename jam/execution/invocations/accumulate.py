from typing import Any, Dict, Tuple
from tsrkit_types import U32
from jam.state.partial import GhostPartial
from jam.types.state.accumulation.types import (
    DeferredTransfers,
    OperandTuples,
    AccuContextX,
    AccumulationContext,
    PreimageDict,
)
from jam.execution.invocations.arg_invoke import PsiM
from jam.execution.invocations.functions.general_fns import GeneralFunctions
from jam.execution.invocations.protocol import InvocationInfo, InvocationProtocol
from tsrkit_types.null import Null
from tsrkit_types.integers import Uint
from jam.types.protocol.core import Gas, ServiceId, TimeSlot
from jam.types.protocol.crypto import Hash, OpaqueHash
from jam.types.protocol.merkle import OptionHash
from jam.execution.invocations.functions.accumulate_fns import (
    AccumulateFunctions,
    check,
)
from tsrkit_pvm import ExecutionStatus
from jam.utils.constants import MAX_SERVICE_CODE_SIZE


class PsiA(InvocationProtocol):
    def __init__(self, u: GhostPartial, t: TimeSlot, s: ServiceId, g: Gas, o: OperandTuples, entropy: OpaqueHash):
        self.partial_state = u
        self.timeslot = t
        self.service_id = s
        self.gas = g
        self.operandTuples = o
        self.entropy = entropy
        self.context = AccumulationContext(x=self.initializer_fn(s, u.clone(), t), y=self.initializer_fn(s, u.clone(), t))
        self.table = self.build_table(s, self.context.x.partial_state.service_accounts)

    def build_table(self, 
        xs: int,
        delta: Dict[int, Any]
    ) -> Dict[int, InvocationInfo]:
        return {
            # fetch
            1: (
                GeneralFunctions,
                {  
                    "package": None,
                    "entropy": self.entropy,
                    "trace": None,
                    "item_index": None,
                    "import_segments": None,
                    "extrinsics": None,
                    "o": self.operandTuples,
                    "t": None,
                },
            ),
            # gas (Returns the gas remaining)
            0: (GeneralFunctions, {}),  
            # lookup
            2: (
                GeneralFunctions,
                {"service_data": delta[xs], "service_index": xs, "accounts": delta},
            ),  
            # read
            3: (
                GeneralFunctions,
                {"service_data": delta[xs], "service_index": xs, "accounts": delta},
            ),
            # write
            4: (
                GeneralFunctions,
                {"service_data": delta[xs], "service_index": xs},
            ),
            5: (GeneralFunctions, {"service_index": xs, "accounts": delta}),  # info
            # bless (Updates previlaged accounts)
            14: (AccumulateFunctions, {}),
            # assign (Updates authorizer_keys/Phi)
            15: (AccumulateFunctions, {}),
            # designate (Updates validator_keys/Iota)
            16: (AccumulateFunctions, {}),
            # checkpoint (fn to update the context[y])
            17: (AccumulateFunctions, {}),
             # new (Updates the delta with a new service)
            18: (AccumulateFunctions, {"block_timeslot": self.timeslot}),
            # upgrade (Updates the service account)
            19: (AccumulateFunctions, {}),
            # transfer (Updates service deferred transfers & balance)
            20: (
                AccumulateFunctions,
                {},
            ),  
            # eject (Removal of service account)
            21: (
                AccumulateFunctions,
                {"block_timeslot": self.timeslot},
            ),  
            # query (Updates registers[7,8] wrt AccountLookup)
            22: (
                AccumulateFunctions,
                {},
            ),  
            # solicit (Updated the AccountLookup)
            23: (AccumulateFunctions, {"block_timeslot": self.timeslot}),  
            # forget (Updates lookupTimestamp & preimage)
            24: (AccumulateFunctions, {"block_timeslot": self.timeslot}),  
            # yield_ (Updates context[x]_hash)
            25: (AccumulateFunctions, {}),  
            # provide (Updates preimage)
            26: (AccumulateFunctions, {"service_id": xs}),  
            # log
            # TODO: Add core_index
            100: (
                GeneralFunctions,
                {"core_index": 0, "service_id": self.service_id},
            ),  
        }

    def execute(self):
        meta_n_code = self.partial_state.service_accounts[self.service_id].m_c()
        if meta_n_code is None or len(meta_n_code[1]) > MAX_SERVICE_CODE_SIZE:
            return self.partial_state, DeferredTransfers([]), None, Gas(0), set()
        else:
            gas, status, context = PsiM.execute(
                meta_n_code[1],
                5,
                int(self.gas),
                Uint(self.timeslot).encode()
                + Uint(self.service_id).encode()
                + Uint(len(self.operandTuples)).encode(),
                self.dispatch,
                self.context,
            )
            return self.collapse(status, gas, context)

    @staticmethod
    def initializer_fn(s: ServiceId, state_context: GhostPartial, timeslot: TimeSlot) -> AccuContextX:
        """
        Take Service id and Account to yield a "mutator context" - this is to make sure no changes to actual state are made if we exit
        Args:
            s: Service ID
            state_context: Partial State

        Returns:
            Mutator context
        """
        from jam.state.state import state

        value = (
            U32.decode(
                Hash.blake2b(
                    Uint(s).encode() + state.eta[0].encode() + Uint(state.tau).encode()
                )
            ) % (2**32 - 2**9)
        ) + 2**8
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
        status: ExecutionStatus | bytes, gas: Gas, context: AccumulationContext
    ) -> Tuple[GhostPartial, DeferredTransfers, OptionHash, Gas, PreimageDict]:
        """
        Selects X / Y depending if HALT or PvmError
        Args:
            status: Execution status
            gas: Consumed Gas
            context: X, Y

        Returns:
            GhostPartial, DeferredTransfers, OptionHash, Gas, PreimageDict
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
