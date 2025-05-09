from jam.accumulation.types import StateContext, OperandTuple
from jam.pvm.extract import Status
from typing import Optional, Tuple
from jam.types.base.sequences.bytes import ByteArray32, Byte, Bytes
from jam.hostCall.types import XContent, DeferredTransfers
from jam.types.protocol.core import Balance, Gas, ServiceId, TimeSlot
from jam.pvm.register import Registers
from jam.pvm.pvm_memory import PageMemory
from jam.state.components.delta import AccountData, Delta
from jam.types.protocol.crypto import Entropy
from hashlib import blake2b
from jam.hostCall.process import HostCall
from jam.hostCall.invocation import PsiM
from jam.types.base.integers.fixed import U32, U64, U256
from jam.utils.constants import ADDITIONAL_BALANCE_PER_ITEM, ADDITIONAL_BALANCE_PER_OCTET, BASIC_MINIMUM_BALANCE
from tests.fixtures.utils import create_dummy_bytes32
from tests.unit.accumulation.types import StateContext, OperandTuples

#Find the a_t of a Service Account
# https://graypaper.fluffylabs.dev/#/9a08063/112701116701?v=0.6.6
def fetch_t(account:AccountData):
    a_i = 2 * len(account.lookup) + len(account.storage)
    a_o=0
    for hash,length in account.lookup:
        a_o+=81+length
    for code in account.storage:
        a_o+=31+len(code)
    a_t = BASIC_MINIMUM_BALANCE + ADDITIONAL_BALANCE_PER_ITEM * a_i + a_o*ADDITIONAL_BALANCE_PER_OCTET
    return a_t

def check(u:StateContext,i:ServiceId):
    if u.service_accounts[i] is None:
        return i;
    else:
        return check(u,(i-2**8)%(2**32-2**9)+2**8)

def i_function(u: StateContext, s: ServiceId, _n_o: Entropy, timeslot: TimeSlot) -> XContent:
    first = bytes(s.encode())
    second = bytes(_n_o.encode())
    third = bytes(timeslot.encode())
    hashed = ByteArray32(blake2b(first + second + third, digest_size=32).digest())
    # value = ByteArray32.decode_from(hashed)[0]
    buffer = bytes()
    value = ByteArray32.decode_from(bytes(hashed))
    i = HostCall.check(u.service_accounts.keys(), value)
    result = XContent(
        s_index=s,
        partial_state=u,
        i_index=i,
        deferred_transfers=[],
        hash=None
    )
    return result


def c_function(g: Gas,  o: Optional[Bytes] = Status, context: Optional[Tuple[XContent, XContent]] = None) -> (
        Tuple)[StateContext, DeferredTransfers, Optional[ByteArray32], Gas]:
    if context is not None:
        x, y = context
    else:
        x, y = None, None
    print("inside c_function:", g, o, x, y)
    if o == Status.PANIC or o == Status.OUT_OF_GAS:
        return y.partial_state, y.deferred_transfers, y.hash, g
    elif isinstance(o, ByteArray32):
        return x.partial_state, x.deferred_transfers, o, g
    else:
        return x.partial_state, x.deferred_transfers, x.hash, g


def g_function(status: Status, gas: Gas, register: Registers, memory: PageMemory, service: AccountData, x: XContent, y: XContent) -> (
        Tuple)[Status, Gas, Registers, PageMemory, XContent, XContent]:
    x.partial_state.delta[x.s_index] = service
    return status, gas, register, memory, x, y


class PsiA:
    header_timeslot = TimeSlot(2)
    entropy = create_dummy_bytes32()
    def __init__(self, u: StateContext,
                 t: TimeSlot, s: ServiceId, g: Gas, o: OperandTuples):
        self.partial_state = u
        self.timeslot = t
        self.service_id = s
        self.gas = g
        self.operands = o
        self.f_function = self.accumulate_f()

    def process(self):
        # if self.partial_state.service_accounts[self.service_id].code_hash is None:
        if self.partial_state.service_accounts.get(self.service_id) is None or self.partial_state.service_accounts.get(self.service_id).code_hash is None:
            return i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot).partial_state, [], None, 0
        else:
            encoded_value = self.timeslot.encode() + self.service_id.encode() + self.operands.encode()
            return c_function(*PsiM(self.partial_state.service_accounts.get(self.service_id).code_hash, 5, self.gas, encoded_value, self.f_function, (i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot), i_function(self.partial_state, self.service_id, self.entropy, self.header_timeslot))).process())

    def accumulate_f(self):

        def read(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
            return g_function(*HostCall.read(call), x=x, y=y)

        def write(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index)
            return g_function(*HostCall.write(call), x=x, y=y)

        def lookup(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
            return g_function(*HostCall.lookup(call), x=x, y=y)

        def gas(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.gas(call)

        def info(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, service=x.partial_state.service_accounts[x.s_index], s_index=x.s_index, delta=x.partial_state.delta)
            return g_function(*HostCall.info(call), x=x, y=y)

        def bless(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.bless(call)

        def assign(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.assign(call)

        def designate(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.designate(call)

        def checkpoint(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.checkpoint(call)

        def new(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.new(call)

        def upgrade(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.upgrade(call)

        def transfer(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.transfer(call)

        def eject(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.eject(call)

        def query(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall.query(call)

        def solicit(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y, timeslot=self.timeslot)
            return HostCall.solicit(call)

        def forget(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y, timeslot=self.timeslot)
            return HostCall.forget(call)

        def _yield(_gas: Gas, register: Registers, memory: PageMemory, x: XContent, y: XContent):
            call = HostCall(gas=_gas, register=register, memory=memory, xcontext=x, ycontext=y)
            return HostCall._yield(call)

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
            "bless": bless, 5: bless,
            "assign": assign, 6: assign,
            "designate": designate, 7: designate,
            "gas": gas, 0: gas,
            "checkpoint": checkpoint, 8: checkpoint,
            "new": new, 9: new,
            "upgrade": upgrade, 10: upgrade,
            "transfer": transfer, 11: transfer,
            "eject": eject, 12: eject,
            "query": query, 13: query,
            "solicit": solicit, 14: solicit,
            "forget": forget, 15: forget,
            "yield": _yield, 16: _yield
        }

        def get_function(n):
            return function_map.get(n, default)  # Default function if `n` not found

        return get_function  # Return the dynamic function selector
