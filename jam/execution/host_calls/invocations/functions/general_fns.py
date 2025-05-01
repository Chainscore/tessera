
from jam.execution.host_calls.invocations.functions.protocol import InvocationFunctions as INVF
from jam.execution.host_calls.invocations.protocol import Context, DispatchNormalReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import ExecutionStatus
from jam.types.protocol.core import Gas


class GeneralFunctions(INVF):

    @INVF.register(0, gas_cost=10)
    def gas(cls, gas: Gas, registers: Registers, memory: Memory, context: Context) -> DispatchNormalReturn:
        registers[7] = gas
        return ExecutionStatus.CONTINUE, gas, registers, memory, context

    @INVF.register(1, gas_cost=10)
    def lookup(cls, gas: Gas, registers: Registers, memory: Memory, s: int, s_: int, d: dict):
        delta_keys = initial_delta.keys()
        # Calculate `a`
        a = None
        if self.initial_service_index <= self.initial_regs[6] <= 2**64-1:
            a = self.initial_service_account
        elif self.initial_regs[6] in delta_keys:
            key = str(self.initial_regs[6])
            a = self.initial_delta[key]
        h, o = self.initial_regs[8], self.initial_regs[9]

        values = InstructionMapper.memory_value(self.initial_memory, h, 32)
        _hex = HostCall.get_hex_string(Bytes(values))
        byte_value = bytes.fromhex(_hex[2:])  # [2:] removes "0x"
        hashed = "0x" + blake2b(byte_value, digest_size=32).hexdigest()

        is_p, a_p = HostCall.search_p(a.lookup, hashed)
        ap_keys = a.lookup.keys()
        if not InstructionMapper.valid_address(self.initial_memory, h, 32):
            v = "error"
        elif a is None or hashed not in ap_keys:
            v = None
        else:
            v = a_p

        if isinstance(v, list):
            f = min(self.initial_regs[9], len(v))
            _l = min(self.initial_regs[10], len(v) - f)
        else:
            f = self.initial_regs[9]
            _l = self.initial_regs[10]

        if v == "error" or not InstructionMapper.valid_address(self.initial_memory, o, _l, True):
            self.initial_regs[6] = 2**64 - 3
            return self
        elif v is None:
            self.initial_regs[6] = 2**64 - 1
        else:
            self.initial_regs[6] = len(v)
            self.initial_memory = InstructionMapper.store_value(self.initial_memory, o, v)
        return self
