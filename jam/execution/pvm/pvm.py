from dataclasses import dataclass
from typing import Tuple
from jam.execution.pvm.instructions.table_map import InstTableMap
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.program import Program
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import OUT_OF_GAS, PAGE_FAULT, PANIC, ExecutionStatus, PvmError
from jam.types.base.integers.fixed import U8
from jam.types.protocol.core import Gas, ProgramCounter, Register, RemainingGas

@dataclass
class PVM:

    @classmethod
    def execute(
        cls,
        blob: bytes,
        program_counter: ProgramCounter,
        gas: Gas,
        registers: Registers,
        memory: Memory
    ) -> Tuple[ExecutionStatus, ProgramCounter, RemainingGas, Registers, Memory]:
        """
        Execute the program blob `p` as per Psi specification.

        Args:
            blob: Program blob
            program_counter: Initial program counter
            gas: Gas provided for execution
            registers: Initial registers
            memory: Initial memory

        Returns:
            ExecutionStatus: Status of the execution - Either PANIC, HALT, PAGE-FAULT, HOST, OUT-OF-GAS, or CONTINUE
            U32: Final program counter
            RemainingGas: Remaining gas
            Registers: Final registers
            Memory: Final memory
        """
        program, _ = Program.decode_from(blob)
        remaining_gas = int(gas)
        # print("# \t Inst \t  Bitmask ")
        # for i, inst in enumerate(program.instruction_set[int(program_counter):]):
        #     print(f"{i} \t {inst} \t {"✅" if program.offset_bitmask[i] else ""}")
        while True:
            try:
                opcode: U8 = program.zeta[program_counter]
                table = InstTableMap.get_instructions_table(opcode)(counter=program_counter, program=program)

                print(f"🤖 {int(program_counter)} | ⛽️ {remaining_gas} | {table.table()[opcode].name} ({opcode}) on {table.__class__.__name__}")
                status, program_counter, registers, memory = table.execute(opcode, registers, memory)
                remaining_gas -= int(table.table()[opcode].gas)
                # print([int(r) for r in registers])
                # print(f"Status: {status} | Gas: {remaining_gas} | PC: {program_counter}")
                if remaining_gas < 0:
                    return OUT_OF_GAS, program_counter, remaining_gas, registers, memory
                elif status == ExecutionStatus.HALT or status == ExecutionStatus.HOST:
                    return status, program_counter, remaining_gas, registers, memory

            except PvmError as e:
                if e.code == PANIC:
                    return PANIC, program_counter, remaining_gas, registers, memory
                elif e.code == ExecutionStatus.PAGE_FAULT:
                    return PAGE_FAULT(Register(e.code.value.register.get_value())), program_counter, remaining_gas, registers, memory
                else:
                    raise e
