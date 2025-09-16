from typing import Tuple
from tsrkit_types import Uint
from jam.execution.invocations.arg_invoke import PsiM
from jam.execution.invocations.functions.general_fns import GeneralFunctions
from jam.execution.invocations.protocol import InvocationProtocol
from jam.execution.utils import decode_code_hash
from jam.state.accounts import DeltaView
from jam.types.state.accumulation.types import DeferredTransfers
from jam.types.state.delta import AccountData
from jam.types.protocol.core import Gas, ProgramCounter, ServiceId, TimeSlot
from jam.utils.constants import W_C


class PsiT(InvocationProtocol):
    def __init__(self, d: DeltaView, block_timeslot: TimeSlot, s: ServiceId, transfers: DeferredTransfers):
        self.delta = d
        self.timeslot = block_timeslot
        self.service_id = s
        self.transfers: DeferredTransfers = transfers
        self.table = self.build_table()

    def build_table(self):
        from jam.state.state import state

        return {
            0: (GeneralFunctions, {}),
            1: (
                GeneralFunctions,
                {
                    "package": None,
                    "entropy": state.eta[0],
                    "trace": None,
                    "item_index": None,
                    "import_segments": None,
                    "extrinsics": None,
                    "o": None,
                    "t": self.transfers,
                },
            ),
            2: (
                GeneralFunctions,
                {
                    "service_data": self.delta[self.service_id],
                    "service_index": self.service_id,
                    "accounts": state.delta,
                },
            ),
            # read
            3: (
                GeneralFunctions,
                {"service_data": self.delta[self.service_id], "service_index": self.service_id, "accounts": self.delta},
            ),
            # write
            4: (
                GeneralFunctions,
                {"service_data": self.delta[self.service_id], "service_index": self.service_id},
            ),
            # info
            5: (GeneralFunctions, {"service_index": self.service_id, "accounts": self.delta}),  # info
            # TODO: Add core_index [we'll probably be storing core_index in node info]
            100: (
                GeneralFunctions,
                {"core_index": 0, "service_id": self.service_id},
            ),  # log
        }

    def execute(self) -> Tuple[AccountData, Gas]:
        service = self.delta[self.service_id]
        _, pc = decode_code_hash(
            service.historical_lookup(
                self.timeslot,
                service.service.code_hash
            )
        )

        service.service.balance = service.service.balance + Gas(sum(int(t.amount) for t in self.transfers))

        if len(self.transfers) == 0 or pc is None or 0 == len(pc) > W_C:
            return service, Gas(0)

        args = (
            Uint(self.timeslot).encode()
            + Uint(self.service_id).encode()
            + Uint(len(self.transfers)).encode()
        )
        u, _, _ = PsiM.execute(
            pc,
            ProgramCounter(10),
            sum(int(t.gas) for t in self.transfers),
            args,
            self.dispatch,
            None
        )

        return service, Gas(u)
