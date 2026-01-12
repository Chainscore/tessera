from jam.execution.invocations.functions.general_fns import GeneralFunctions
from jam.execution.invocations.arg_invoke import PsiM
from jam.execution.invocations.protocol import InvocationProtocol
from jam.types.protocol.core import CoreIndex, ProgramCounter
from jam.types.protocol.crypto import OpaqueHash
from jam.types.work import WorkPackage
from jam.utils.constants import IS_AUTHORIZED_GAS, MAX_AUTH_CODE_SIZE
from tsrkit_pvm import HostStatus
from jam.types.work.execution import WorkExecResult
from tsrkit_types.null import Null


class PsiI(InvocationProtocol):
    def __init__(self, p: WorkPackage, c: CoreIndex):
        self.work_package = p
        self.core = c
        self.table = self.build_table()

    def build_table(self):
        return {
            0: (GeneralFunctions, {}),
            1: (
                GeneralFunctions,
                {
                    "package": self.work_package,
                    "entropy": OpaqueHash([0] * 32),
                    "trace": None,
                    "item_index": None,
                    "import_segments": None,
                    "extrinsics": None,
                    "o": None,
                    "t": None,
                },
            ),
            100: (GeneralFunctions,
                  {"core_index": self.core, "service_id": self.work_package.auth_code_host}
                ),  # log
        }

    def execute(self):
        from jam.state.state import state

        # pc == pu
        _, pc = self.work_package.m_c(state.delta)

        if pc is None:
            return WorkExecResult(Null, key="bad_code"), 0
        elif len(pc) > MAX_AUTH_CODE_SIZE:
            return WorkExecResult(Null, key="code_oversize"), 0
        
        u, r, _ = PsiM.execute(
            blob=pc,
            pc=0,
            gas=IS_AUTHORIZED_GAS,
            arguments=self.core.encode(),
            dispatch_fn=self.dispatch,
            context=None,
        )

        return r, u
