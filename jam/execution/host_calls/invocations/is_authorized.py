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
            0: (GeneralFunctions, ()),
            18: (GeneralFunctions, (self.work_package, OpaqueHash([0] * 32)))
        }

    def execute(self):
        _, pc = self.work_package.m_c
        PsiM(
            pc,
            ProgramCounter(0),
            IS_AUTHORIZED_GAS,
            self.core.encode(),
            self.dispatch,
            None,
        )