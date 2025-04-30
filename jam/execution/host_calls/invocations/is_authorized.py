from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.protocol import InvocationProtocol
from jam.types.protocol.core import CoreIndex, ProgramCounter
from jam.types.work.package import WorkPackage
from jam.utils.constants import IS_AUTHORIZED_GAS


class PsiI(InvocationProtocol):
    def __init__(self, p: WorkPackage, c: CoreIndex):
        self.work_package = p
        self.core = c

    def table(cls):
        return {
            0: (GeneralFunctions, ())
        }

    def execute(self):
        buffer = self.work_package.encode() + self.core.encode()
        PsiM(
            self.work_package.code_hash, # TODO: update this
            ProgramCounter(0),
            IS_AUTHORIZED_GAS,
            buffer,
            self.dispatch,
            None,
        )