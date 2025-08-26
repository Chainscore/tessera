from typing import Tuple

from tsrkit_types import Bytes, Null
import time 
from jam.execution.invocations.functions.general_fns import GeneralFunctions
from jam.execution.invocations.arg_invoke import PsiM
from jam.execution.invocations.functions.refine_fns import (
    RefineFunctions,
    RefineContext,
    RefinementMap,
)
from jam.execution.invocations.protocol import InvocationProtocol
from tsrkit_pvm import OUT_OF_GAS, PANIC
from jam.execution.utils import decode_code_hash
from tsrkit_types.integers import Uint

from jam.types.work import WorkExecResult, Segments, WorkPackage
from jam.types.protocol.core import ProgramCounter, Gas
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.utils.constants import REFINE_GAS


class PsiR(InvocationProtocol):
    def __init__(
        self,
        item_index: int,
        p: WorkPackage,
        auth_trace: bytes,
        i_segments: [[bytes]],
        e_offset: int,
    ):
        self.item_index = Uint[16](item_index)
        self.work_package = p
        self.auth_trace = auth_trace
        self.i_segments = i_segments
        self.e_offset = e_offset

    @property
    def wi(self):
        return self.work_package.items[self.item_index]

    def table(self):
        from jam.state.state import state
        from jam.storage.item_extrinsics import ItemExtrinsics
        from jam.settings import settings

        return {
            0: (GeneralFunctions, {}),
            17: (
                RefineFunctions,
                {
                    "service_id": self.wi.service,
                    "delta": state.delta,
                    "timeslot": self.work_package.context.lookup_anchor_slot,
                },
            ),
            18: (
                GeneralFunctions,
                {
                    "package": self.work_package,
                    "entropy": OpaqueHash([0] * 32),
                    "trace": self.auth_trace,
                    "item_index": self.item_index,
                    "import_segments": self.i_segments,
                    "extrinsics": ItemExtrinsics(settings.main_db).get_all(self.work_package),
                    "o": None,
                    "t": None,
                },
            ),
            19: (RefineFunctions, {"export_segment_offset": self.e_offset}),
            20: (RefineFunctions, {}),
            21: (RefineFunctions, {}),
            22: (RefineFunctions, {}),
            23: (RefineFunctions, {}),
            24: (RefineFunctions, {}),
            25: (RefineFunctions, {}),
            26: (RefineFunctions, {}),
            # TODO: Add core_index [we'll probably be storing core_index in node info]
            100: (
                GeneralFunctions,
                {"core_index": 0, "service_id": self.wi.service},
            ),  # log
        }

    def execute(self) -> Tuple[WorkExecResult, Segments, Gas]:
        from jam.state.state import state

        _, pc = decode_code_hash(
            state.delta[self.wi.service].historical_lookup(
                self.work_package.context.lookup_anchor_slot, self.wi.code_hash
            )
        )
        args = (
            Uint(self.wi.service).encode()
            + self.wi.payload.encode()
            + bytes(Hash.blake2b(self.work_package.encode()))
            + self.work_package.context.encode()
            + self.work_package.authorizer.code_hash.encode()
        )
        print("Executing PsiR with args:", args.hex())
        start = time.time()
        u, r, context = PsiM.execute(
            pc,
            ProgramCounter(0),
            REFINE_GAS,
            args,
            self.dispatch,
            RefineContext(m=RefinementMap({}), e=Segments([])),
        )
        print(
            f"PsiR execution completed in {time.time() - start:.2f} seconds, gas used: {u}, result: {r.hex() if isinstance(r, bytes) else r}"
        )
        if r == PANIC:
            return WorkExecResult(Null, key="panic"), Segments([]), Gas(u)

        elif r == OUT_OF_GAS:
            return WorkExecResult(Null, key="out_of_gas"), Segments([]), Gas(u)

        return WorkExecResult(Bytes(r), key="ok"), Segments(context.e), Gas(u)
