from typing import Tuple
from jam.pvm.instructions.table_map import InstTableMap
from jam.pvm.memory import Memory
from jam.pvm.program import Program
from jam.pvm.register import Registers
from jam.pvm.status import HALT, PAGE_FAULT, PANIC, ExecutionStatus, ExecutionStatusCode
from jam.types.base.integers.fixed import U8
from jam.types.protocol.core import Gas, ProgramCounter, Register, RemainingGas
from jam.pvm.errors import PvmError, PvmErrorCodes

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
        print("Program")
        print(f"Jump Table : {program.jump_table}")
        for i in range(len(program.instruction_set)):
            print(f"Inst | {i} \t | {"✅" if program.offset_bitmask[i] else "⏭️ "} {program.instruction_set[i]}")
        while True:
            try:
                opcode: U8 = program.zeta[program_counter]
                table = InstTableMap.get_instructions_table(opcode)(counter=program_counter, program=program)
                print(f"\nExecuting {opcode} - {table.table()[int(opcode)].name}")
                print(f"Program Counter: {program_counter}")
                status, program_counter, registers, memory = table.execute(opcode, registers, memory)

                if status.code == ExecutionStatusCode.HALT:
                    return status, program_counter, gas, registers, memory
                print(f"Opcode status: {status.code} | Next: {int(program_counter)} - {program.zeta[program_counter]}")
            except PvmError as e:
                print("Exit condition e", e)
                if e.code == PvmErrorCodes.PANIC:
                    return PANIC, program_counter, gas, registers, memory
                elif e.code == PvmErrorCodes.PAGE_FAULT:
                    return PAGE_FAULT(Register(0)), program_counter, gas, registers, memory
                elif e.code == PvmErrorCodes.INVALID_OPCODE:
                    return PANIC, program_counter, gas, registers, memory
                else:
                    raise e
