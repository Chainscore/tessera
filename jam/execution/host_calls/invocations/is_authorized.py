from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.protocol import InvocationProtocol
from jam.types.protocol.core import CoreIndex, ProgramCounter
from jam.types.protocol.crypto import OpaqueHash
from jam.types.work.package import WorkPackage
from jam.utils.constants import IS_AUTHORIZED_GAS


class PsiI(InvocationProtocol):
    def __init__(self, p: WorkPackage, c: CoreIndex):
        self.work_package = p
        self.core = c

    def table(self):
        return {
            0: (GeneralFunctions, {}),
            18: (GeneralFunctions, {
                    "package": self.work_package,
                    "entropy": OpaqueHash([0] * 32),
                    "trace": None,
                    "item_index": None,
                    "import_segments": None,
                    "extrinsics": None,
                    "o": None,
                    "t": None
                    }
                 )
        }

    def execute(self):
        from jam.state.state import state

        _, pc = self.work_package.m_c(state.delta)
        u, r, _ = PsiM.execute(
            blob=pc,
            pc=ProgramCounter(0),
            gas=IS_AUTHORIZED_GAS,
            arguments=self.core.encode(),
            dispatch_fn=self.dispatch,
            context=None,
        )
        return (r, u)