from typing import Tuple, TYPE_CHECKING

import structlog

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

if TYPE_CHECKING:
    from jam.jam_node import JamNode

logger = structlog.get_logger("pvm")

class PsiR(InvocationProtocol):
    def __init__(
        self,
        core_index: int,
        item_index: int,
        p: WorkPackage,
        auth_trace: bytes,
        i_segments: list[list[bytes]],
        e_offset: int,
        jam: "JamNode"
    ):
        self.core_index = core_index
        self.item_index = Uint[16](item_index)
        self.work_package = p
        self.auth_trace = auth_trace
        self.i_segments = i_segments
        self.e_offset = e_offset
        self.jam = jam
        self.table = self.build_table()

    @property
    def wi(self):
        return self.work_package.items[self.item_index]


    def build_table(self):
        from jam.storage.item_extrinsics import ItemExtrinsics
        state = self.jam.state
        settings = self.jam.settings

        return {
            0: (GeneralFunctions, {}),
            1: (
                GeneralFunctions,
                {
                    "package": self.work_package,
                    "entropy": OpaqueHash([0] * 32),
                    "trace": self.auth_trace,
                    "item_index": self.item_index,
                    "import_segments": self.i_segments,
                    "extrinsics": ItemExtrinsics(settings.main_db).get_all(self.work_package),
                    "o": None,
                },
            ),
            6: (
                RefineFunctions,
                {
                    "service_id": self.wi.service,
                    "delta": state.delta,
                    "timeslot": self.work_package.context.lookup_anchor_slot,
                },
            ), # Historial lookup 
            7: (RefineFunctions, {"export_segment_offset": self.e_offset}),
            8: (RefineFunctions, {}),
            9: (RefineFunctions, {}),
            10: (RefineFunctions, {}),
            11: (RefineFunctions, {}),
            12: (RefineFunctions, {}),
            13: (RefineFunctions, {}),
            100: (
                GeneralFunctions,
                {"core_index": self.core_index, "service_id": self.wi.service},
            ),  # log
        }

    def execute(self) -> Tuple[WorkExecResult, Segments, Gas]:
        state = self.jam.state
        t0 = time.time()

        account = state.delta[self.wi.service]
        if account is None:
            raise ValueError(f"Service {int(self.wi.service)} not found in state")

        code = account.historical_lookup(
            self.work_package.context.lookup_anchor_slot, self.wi.code_hash
        )
        if code is None:
            raise ValueError(f"Code not found via historical_lookup for service {int(self.wi.service)}")
        t1 = time.time()

        _, pc = decode_code_hash(code)
        t2 = time.time()

        args = (
            Uint(self.core_index).encode()
            + Uint(self.item_index).encode()
            + Uint(self.wi.service).encode()
            + self.wi.payload.encode()
            + bytes(Hash.blake2b(self.work_package.encode()))
        )

        try:
            u, r, context = PsiM.execute(
                pc,
                0,
                REFINE_GAS,
                args,
                self.dispatch,
                RefineContext(m=RefinementMap({}), e=Segments([])),
            )
        except Exception as e:
            logger.error("REFINE INVOCATION ERR", err=str(e))
            raise e
        t3 = time.time()

        logger.trace("REFINE_TIMING",
            lookup_ms=int((t1 - t0) * 1000),
            decode_ms=int((t2 - t1) * 1000),
            execute_ms=int((t3 - t2) * 1000),
            total_ms=int((t3 - t0) * 1000),
            code_size=len(code) if code else 0,
            service=int(self.wi.service),
        )

        if r == PANIC:
            return WorkExecResult(Null, key="panic"), Segments([]), Gas(u)

        elif r == OUT_OF_GAS:
            return WorkExecResult(Null, key="out_of_gas"), Segments([]), Gas(u)

        return WorkExecResult(Bytes(r), key="ok"), Segments(context.e), Gas(u)
