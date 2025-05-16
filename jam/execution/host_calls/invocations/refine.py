from jam.execution.host_calls.invocations.functions.general_fns import GeneralFunctions
from jam.execution.host_calls.invocations.arg_invoke import PsiM
from jam.execution.host_calls.invocations.functions.refine_fns import RefineFunctions
from jam.execution.host_calls.invocations.protocol import InvocationProtocol
from jam.execution.utils import decode_code_hash
from jam.state.state import state
from jam.storage.item_extrinsics import ItemExtrinsics
from jam.types.base import U16
from jam.types.protocol.core import CoreIndex, ProgramCounter
from jam.types.protocol.crypto import OpaqueHash, Hash
from jam.types.work.package import WorkPackage
from jam.utils.constants import IS_AUTHORIZED_GAS


class PsiR(InvocationProtocol):
    def __init__(self, item_index: int, p: WorkPackage, auth_trace: bytes, i_segments: bytes, e_offset: int):
        self.item_index = U16(item_index)
        self.work_package = p
        self.auth_trace = auth_trace
        self.i_segments = i_segments
        self.e_offset = e_offset


    def table(self):
        return {
            0: (GeneralFunctions, ()),
            18: (GeneralFunctions, (self.work_package, OpaqueHash([0] * 32), self.auth_trace, self.item_index, self.i_segments, ItemExtrinsics.get_all(self.work_package))),
            19: (RefineFunctions, (self.e_offset))
        }

    def execute(self):
        wi = self.work_package.items[self.item_index]
        _, pc = decode_code_hash(state.delta[wi.service].historical_lookup(self.work_package.context.lookup_anchor_slot, wi.code_hash))
        args = self.item_index.encode() + wi.service.encode() + wi.payload.encode() + bytes(Hash.blake2b(self.work_package.encode()))
        u, r, (m, e) = PsiM.execute(
            pc,
            ProgramCounter(0),
            IS_AUTHORIZED_GAS,
            args,
            self.dispatch,
            (None, []),
        )
        print(f"u: {u} | r: {r} | (m, e): ({m}, {e})")

    # def process(self):
    #     w = self.work_package.items[self.pc]
    #
    #     if w.service not in self.delta.keys() or historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash) is None:
    #         return "BAD", []
    #     elif len(historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash)) > 4000000:
    #         return "BIG", []
    #     else:
    #         first = w.service.encode()
    #         second = w.payload.encode()
    #         third = "0x" + blake2b(self.work_package).encode()
    #         forth = self.work_package.context.encode()
    #         fifth = self.work_package.authorization.encode() #not confirmed yet
    #         a = first + second + third + forth + fifth
    #         g, r, (m, e) = PsiM(historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash), 0, w.refine_gas_limit, a, self.f_function, (None, [])).process()
    #         if r == Status.OUT_OF_GAS or r == Status.PANIC:
    #             return r, []
    #         else:
    #             return r, e