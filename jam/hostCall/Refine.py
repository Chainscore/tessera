from jam.hostCall.process import HostCall
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.services import historicalLookup
from jam.pvm.register import Registers
from jam.pvm.pvm_memory import PageMemory
from jam.types.protocol.core import Gas
from jam.types.state.delta import Delta
from jam.hostCall.types import RefineMap
from jam.pvm.extract import Status
from jam.types.work.package import WorkPackage
from hashlib import blake2b
from jam.hostCall.invocation import PsiM
from jam.types.work.segment import MultiSegments, Segments


class PsiR:

    delta: Delta
    def __init__(self,
                 i: int,
                 p: WorkPackage,
                 o: Bytes,
                 i_segment: MultiSegments,
                 e_offset: int,
                ):
        self.pc = i
        self.work_package = p
        self.authorizer = o
        self.import_segment = i_segment
        self.offset = e_offset
        self.f_function = self.refine_f()

    def refine_f(self):
        w = self.work_package.items[self.pc]

        def historical_lookup(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export, work_service_id=w.service, delta=self.delta, timeslot=self.work_package.context.lookup_anchor_slot)
            return HostCall.historical_lookup(call)

        def fetch(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export, work_item_index=self.pc, work_package=self.work_package, segment=self.import_segment, offset=self.offset)
            return HostCall.fetch(call)

        def export(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export, offset=self.offset)
            return HostCall.export(call)

        def gas(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.gas(call)

        def machine(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.machine(call)

        def peek(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.peek(call)

        def zero(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.zero(call)

        def poke(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.poke(call)

        def void(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.void(call)

        def invoke(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.invoke(call)

        def expunge(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.expunge(call)

        def default(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segments):
            _gas -= 10
            register[6] = 2 ** 64
            return Status("continue"), _gas, register

        # Dictionary to map `n` to the corresponding function
        function_map = {
            "historical_lookup": historical_lookup, 17: historical_lookup,
            "fetch": fetch, 18: fetch,
            "export": export, 19: export,
            "gas": gas, 0: gas,
            "machine": machine, 20: machine,
            "peek": peek, 21: peek,
            "zero": zero, 23: zero,
            "poke": poke, 22: poke,
            "void": void, 24: void,
            "invoke": invoke, 25: invoke,
            "expunge": expunge, 26: expunge
        }

        def get_function(n):
            return function_map.get(n, default)  # Default function if `n` not found

        return get_function  # Return the dynamic function selector

    def process(self):
        w = self.work_package.items[self.pc]

        if w.service not in self.delta.keys() or historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash) is None:
            return "BAD", []
        elif len(historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash)) > 4000000:
            return "BIG", []
        else:
            first = w.service.encode()
            second = w.payload.encode()
            third = "0x" + blake2b(self.work_package).encode()
            forth = self.work_package.context.encode()
            fifth = self.work_package.authorization.encode() #not confirmed yet
            a = first + second + third + forth + fifth
            g, r, (m, e) = PsiM(historicalLookup(self.delta[w.service], self.work_package.context.lookup_anchor_slot, w.code_hash), 0, w.refine_gas_limit, a, self.f_function, (None, [])).process()
            if r == Status.OUT_OF_GAS or r == Status.PANIC:
                return r, []
            else:
                return r, e






