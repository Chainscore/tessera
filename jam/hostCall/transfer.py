from jam.state.components.delta import AccountData, Delta
from jam.types.protocol.core import Balance, Gas, ServiceId, TimeSlot
from jam.hostCall.types import XContent, PartialState, DeferredTransfers
from jam.pvm.register import Registers
from jam.pvm.pvm_memory import PageMemory
from jam.state.components.delta import AccountData, Delta
from jam.hostCall.process import HostCall
from jam.pvm.extract import Status
from copy import deepcopy
from jam.hostCall.invocation import PsiM


class PsiT:
    def __init__(self, d: Delta, t: TimeSlot, s: ServiceId, bold_t: DeferredTransfers):
        self.delta = d
        self.timeslot = t
        self.service_id = s
        self.transfer = bold_t
        self.f_function = self.transfer_f

    def transfer_f(self):

        def read(_gas: Gas, register: Registers, memory: PageMemory, bold_s: AccountData, s: ServiceId, d: Delta):
            call = HostCall(gas=_gas, register=register, memory=memory, service=bold_s, s_index=s, delta=d)
            return HostCall.read(call)

        def lookup(_gas: Gas, register: Registers, memory: PageMemory, bold_s: AccountData, s: ServiceId, d: Delta):
            call = HostCall(gas=_gas, register=register, memory=memory, service=bold_s, s_index=s, delta=d)
            return HostCall.lookup(call)

        def write(_gas: Gas, register: Registers, memory: PageMemory, bold_s: AccountData, s: ServiceId):
            call = HostCall(gas=_gas, register=register, memory=memory, service=bold_s, s_index=s)
            return HostCall.write(call)

        def gas(_gas: Gas, register: Registers, memory: PageMemory):
            call = HostCall(gas=_gas, register=register, memory=memory)
            return HostCall.gas(call)

        def info(_gas: Gas, register: Registers, memory: PageMemory, s: ServiceId, d: Delta):
            call = HostCall(gas=_gas, register=register, memory=memory, s_index=s, delta=d)
            return HostCall.info(call)

        def default(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            _gas -= 10
            register[6] = 2 ** 64
            return Status("continue"), _gas, register

        # Dictionary to map `n` to the corresponding function
        function_map = {
            "read": read, 2: read,
            "write": write, 3: write,
            "lookup": lookup, 1: lookup,
            "info": info, 4: info,
        }

        def get_function(n):
            return function_map.get(n, default)  # Default function if `n` not found

        return get_function  # Return the dynamic function selector

    def process(self):
        s = deepcopy(self.delta[self.service_id])
        for item in self.transfer:
            s.balance += item.amount
        if s.code_hash is None or self.transfer == []:
            return s
        else:
            gas = 0
            encoded_value = self.timeslot.encode() + self.service_id.encode() + self.transfer.encode()
            for item in self.transfer:
                gas += item.gas
            g, r, _s = PsiM(s.code_hash, 10, gas, encoded_value, self.f_function, s).process()
            return _s

