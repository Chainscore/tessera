from typing import Dict, Tuple

from jam.types import Balance
from tsrkit_types import U32, U64
from jam.state.accounts import DeltaView
from jam.state.partial import GhostPartial
from jam.types.state.accumulation.types import (
    DeferredTransfers,
    AccumulationInputs,
    AccuContextX,
    AccumulationContext,
    PreimageDict,
    DeferredTransfer,
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
from jam.utils.constants import MAX_SERVICE_CODE_SIZE, MINIMUM_SERVICE_INDEX


class PsiA(InvocationProtocol):
    def __init__(
        self,
        u: GhostPartial,
        t: TimeSlot,
        s: ServiceId,
        g: Gas,
        i: AccumulationInputs,
        entropy: OpaqueHash,
    ):
        cloned_state = u.clone(True)

        bal = Balance(0)
        for _i in i:
            _t = _i.unwrap()
            if isinstance(_t, DeferredTransfer):
                bal += _t.amount

        # Credit transfer amounts to receiver's balance
        service_account = cloned_state.service_accounts.get(s)
        old_bal = service_account.service.balance if service_account else Balance(0)

        if service_account:
            service_account.service.balance = old_bal + bal
        elif bal > 0:
            # If service doesn't exist but receiving non-zero balance,
            # we should probably create it or handle it.
            # But spec implies we only process if service exists.
            # Gray Paper: "processed... if destination service exists"
            pass

        self.partial_state = cloned_state
        self.timeslot = t
        self.service_id = s
        self.gas = g
        self.operandTuples = i
        self.entropy = entropy
        self.context = AccumulationContext(
            x=self.initializer_fn(s, cloned_state.clone(True, reset_inherited=False), t, entropy),
            y=self.initializer_fn(s, cloned_state.clone(True, reset_inherited=False), t, entropy),
        )
        self.table = self.build_table(s, self.context.x.partial_state.service_accounts)

    def build_table(self, xs: ServiceId, delta: DeltaView) -> Dict[int, InvocationInfo]:
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
            # bless (Updates privileged accounts)
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
            26: (AccumulateFunctions, {}),
            # log
            # TODO: Add core_index
            100: (
                GeneralFunctions,
                {"core_index": 0, "service_id": self.service_id},
            ),
        }

    def execute(self):
        service_account = self.partial_state.service_accounts.get(self.service_id)
        if service_account is None:
            # If service doesn't exist, we can't execute accumulation logic.
            # Return empty/default result.
            return self.partial_state, DeferredTransfers([]), None, Gas(0), set()

        meta_n_code = service_account.m_c()
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
    def initializer_fn(
        s: ServiceId, state_context: GhostPartial, timeslot: TimeSlot, entropy: OpaqueHash
    ) -> AccuContextX:
        """
        Take Service id and Account to yield a "mutator context" - this is to make sure no changes to actual state are made if we exit
        Args:
            s: Service ID
            state_context: Partial State
            timeslot: Posterior State's Timeslot
            entropy: Posterior State's Eta[0]

        Returns:
            Mutator context
        """
        value = (
            U32.decode(Hash.blake2b(Uint(s).encode() + entropy.encode() + Uint(timeslot).encode()))
            % (2**32 - MINIMUM_SERVICE_INDEX - 2**8)
        ) + MINIMUM_SERVICE_INDEX
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
