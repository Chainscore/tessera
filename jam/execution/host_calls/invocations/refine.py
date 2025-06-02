from typing import Tuple

from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.functions.refine_fns import RefineFunctions, RefineContext, RefinementMap
from jam.execution.host_calls.invocations.protocol import InvocationProtocol
from jam.execution.pvm.status import OUT_OF_GAS, PANIC
from jam.execution.utils import decode_code_hash
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.base import U16, Null, Bytes
from jam.types.protocol.core import ProgramCounter, Gas
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.work.package import WorkPackage
from jam.types.work.manifest import Segments
from jam.types.work.report import WorkExecResult
from jam.utils.constants import IS_AUTHORIZED_GAS


class PsiR(InvocationProtocol):
    def __init__(self, item_index: int, p: WorkPackage, auth_trace: bytes, i_segments: [[bytes]], e_offset: int):
        self.item_index = U16(item_index)
        self.work_package = p
        self.auth_trace = auth_trace
        self.i_segments = i_segments
        self.e_offset = e_offset

    def table(self):
        return {
            0: (GeneralFunctions, ()),
            18: (GeneralFunctions, {
                         "package": self.work_package,
                         "entropy": OpaqueHash([0] * 32),
                         "trace": self.auth_trace,
                         "item_index": self.item_index,
                         "import_segments": self.i_segments,
                         "extrinsics": ItemExtrinsics.get_all(self.work_package),
                         "o": None,
                         "t": None
                     }
                 ),
            19: (RefineFunctions, {
                "export_segment_offset": self.e_offset
            }),
        }

    def execute(self) -> Tuple[WorkExecResult, Segments, Gas]:
        from jam.state.state import state

        wi = self.work_package.items[self.item_index]
        _, pc = decode_code_hash(state.delta[wi.service].historical_lookup(self.work_package.context.lookup_anchor_slot, wi.code_hash))
        args = self.item_index.encode() + wi.service.encode() + wi.payload.encode() + bytes(Hash.blake2b(self.work_package.encode()))
        u, r, context = PsiM.execute(
            pc,
            ProgramCounter(0),
            IS_AUTHORIZED_GAS,
            args,
            self.dispatch,
            RefineContext(m=RefinementMap({}), e=Segments([])),
        )
        if r == PANIC:
            return WorkExecResult({"panic": Null}), Segments([]), Gas(u)
        elif r == OUT_OF_GAS:
            return WorkExecResult({"out_of_gas": Null}), Segments([]), Gas(u)
        return WorkExecResult({"ok": Bytes(r)}), Segments(context.e), Gas(u)