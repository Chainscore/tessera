from jam.execution.host_calls.invocations.invoke import PsiM
from jam.types.protocol.core import CoreIndex
from jam.types.work.package import WorkPackage


class PsiI:
    def __init__(self, p: WorkPackage, c: CoreIndex):
        self.work_package = p
        self.core = c
        self.host_function = self.is_authorized_f()

    def execute(self):
        buffer = self.work_package.encode() + self.core.encode()
        PsiM(
            self.work_package.code_hash,
            U64(0),
            50000000,
            buffer,
            self.dispatch,
            None,
        )

    def dispatch(self):
        def gas(
            _gas: Gas,
            register: Registers,
            memory: PageMemory,
            refine: RefineMap,
            _export: Segments,
        ):
            call = HostCall(
                gas=_gas,
                register=register,
                memory=memory,
                refine=refine,
                export=_export,
            )
            return HostCall.gas(call)

        def default(
            _gas: Gas,
            register: Registers,
            memory: PageMemory,
            refine: RefineMap,
            _export: Segments,
        ):
            _gas -= 10
            register[6] = 2**64
            return Status("continue"), _gas, register, memory

        function_map = {
            "gas": gas,
            0: gas,
        }

        def get_function(n):
            return function_map.get(n, default)  # Default function if `n` not found

        return get_function  # Return the dynamic function selector
