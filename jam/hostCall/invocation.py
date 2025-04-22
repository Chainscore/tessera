from jam.types.base.sequences.bytes import Bytes
from jam.types.protocol.core import Register
from jam.types.protocol.core import ServiceId, Gas
from typing import Any, Union, Tuple, Self, List
from jam.utils.json.serde import JsonSerde
from jam.utils.codec.codable import Codable
from jam.pvm.register import Registers
from jam.pvm.pvm_memory import PageMemory
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from jam.utils.codec.utils import check_buffer_size
from jam.types.base.integers.fixed import U8, U64
from jam.pvm.extract import Status
from jam.pvm.opcode_mapping import InstructionMapper
from jam.pvm.extract import Execution
from jam.pvm.program import Program
from jam.hostCall.decode_prog import derive_p
from jam.types.work.package import WorkPackage
from jam.hostCall.process import HostCall
from jam.hostCall.types import RefineMap, Segment


class PsiM:
    def __init__(self,
                 blob: Bytes,
                 pc: Register,
                 gas: Gas,
                 x_blob: Any,
                 host_function: Any,
                 context: Any
                 ):
        self.blob = blob
        self.pc = pc
        self.gas = gas
        self.x_blob = x_blob
        self.host_function = host_function
        self.context = context

    def process(self):
        print(self.blob)
        res = derive_p(self.blob)
        if res is None:
            return self.gas, Status("panic"), self.context
        (c, w, u) = res
        return RInvocation(*PsiH(c, self.pc, self.gas, w, u, self.host_function, self.context).process()).process()


class RInvocation:
    def __init__(self, status: Status, gas: Gas, registers: Registers, memory: PageMemory, context: Any):
        self.status = status
        self.gas = gas
        self.registers = registers
        self.memory = memory
        self.context = context

    def process(self):
        result = Any
        if self.status == "out-of-gas":
            result = Status("out-of-gas")
        elif self.status == "halt" and InstructionMapper.valid_address(self.memory, self.registers[6], self.registers[7]):
            result = InstructionMapper.memory_value(self.memory, self.registers[6], self.registers[7])
        elif self.status == "halt" and not InstructionMapper.valid_address(self.memory, self.registers[6],
                                                                           self.registers[7]):
            result = Bytes([])
        else:
            result = Status("panic")
        return self.registers, result, self.context


class PsiH:
    def __init__(self, blob: Bytes, pc: Register, gas: Gas, register: Registers, memory: PageMemory, host_function: Any,
                 context: Any):
        self.blob = blob
        self.pc = pc
        self.gas = gas
        self.register = register
        self.memory = memory
        self.host_function = host_function
        self.context = context

    def process(self):
        p = Program.from_json(self.blob)
        pvm = Execution(pc=self.pc, gas=self.gas, initial_registers=self.registers, memory=self.memory, program=p)
        _status, _pc, _gas, _register, _memory = Execution.process_program(pvm)
        if _status == Status.PANIC or _status == Status.OUT_OF_GAS or _status == Status.PAGE_FAULT:
            return _status, _pc, _gas, _register, _memory, self.context
        elif _status == Status.HOST:
            res = self.host_function(_status.number, _gas, _register, _memory, self.context)
            if isinstance(res, Status) and res == Status.PAGE_FAULT:
                return res, _pc, _gas, _register, _memory, self.context
            elif res.status == Status.CONTINUE:
                (_status, _gas, _register, _memory, context) = res
                self.pc = _pc + 1 + PsiH.skip(_pc)
                self.gas = _gas
                self.register = _register
                self.memory = _memory
                self.context = context
                return self.process()
            else:
                return res.status, _pc, res.gas, res.register, res.memory, res.context

    @staticmethod
    def skip(i):
        # function not implemented correctly
        return 24


class PsiI:
    def __init__(self, p: WorkPackage, c: int):
        self.work_package = p
        self.core = c
        self.host_function = self.is_authorized_f()

    def process(self):
        buffer = self.work_package.encode()
        PsiM(self.work_package.code_hash, U64(0), 50000000, buffer, self.host_function, None).process()

    def is_authorized_f(self):
        def gas(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
            call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
            return HostCall.gas(call)

        def default(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
            _gas -= 10
            register[6] = 2 ** 64
            return Status("continue"), _gas, register, memory

        function_map = {
            "gas": gas, 0: gas,
        }

        def get_function(n):
            return function_map.get(n, default)  # Default function if `n` not found

        return get_function  # Return the dynamic function selector




