from jam.hostCall.process import HostCall
import json
from jam.types.base.sequences.bytes.bytes import Bytes
from hashlib import blake2b
import os
from jam.utils.codec.primitives.integers import IntegerCodec
from jam.types.base.integers.fixed import U32, U64, U256
from jam.services import historicalLookup
from jam.pvm.opcode_mapping import InstructionMapper
from jam.pvm.extract import Execution
from jam.pvm.program import Program
from jam.types.base.dictionary import DictionaryCodec
import copy
from jam.pvm.register import Registers
from jam.pvm.pvm_memory import PageMemory
from jam.types.protocol.core import Balance, Gas, ServiceId
from jam.state.components.delta import AccountData, Delta
from jam.hostCall.types import XContent, RefineMap, Segment
from jam.pvm.extract import Status
from jam.types.work.package import WorkPackage
from typing import Optional


def refine_f(n):
    def historical_lookup(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.historical_lookup(call)

    def fetch(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.fetch(call)

    def export(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.export(call)

    def gas(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.gas(call)

    def machine(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.machine(call)

    def peek(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.peek(call)

    def zero(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.zero(call)

    def poke(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.poke(call)

    def void(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.void(call)

    def invoke(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.invoke(call)

    def expunge(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        call = HostCall(gas=_gas, register=register, memory=memory, refine=refine, export=_export)
        return HostCall.expunge(call)

    def default(_gas: Gas, register: Registers, memory: PageMemory, refine: RefineMap, _export: Segment):
        _gas -= 10
        register[6] = 2**64
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

    return function_map.get(n, default)  # Return the corresponding function or default
