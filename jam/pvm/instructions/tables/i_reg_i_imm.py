from math import floor
from typing import Any, Callable, Dict
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec


class InstructionsWArgs1Reg1Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def lx(self) -> int:
        return min(4, max(0, self.skip_index - 1))
    
    @property
    def vx(self) -> int:
        start = self.counter + 2
        end = start + self.lx
        return PvmUtilities.chi(
            IntegerCodec.decode_from(
                self.lx, 
                self.program.zeta[start:end]
            )[0], 
            self.lx
        )

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            50: OpCode(name="jump_ind", fn=cls.jump_ind, gas=Gas(0), is_terminating=True),
            51: OpCode(name="load_imm", fn=cls.load_imm, gas=Gas(0), is_terminating=False),
            52: OpCode(name="load_u8", fn=cls.load_u(8), gas=Gas(0), is_terminating=False),
            53: OpCode(name="load_i8", fn=cls.load_i(8), gas=Gas(0), is_terminating=False),
            54: OpCode(name="load_u16", fn=cls.load_u(16), gas=Gas(0), is_terminating=False),
            55: OpCode(name="load_i16", fn=cls.load_i(16), gas=Gas(0), is_terminating=False),
            56: OpCode(name="load_u32", fn=cls.load_u(32), gas=Gas(0), is_terminating=False),
            57: OpCode(name="load_i32", fn=cls.load_i(32), gas=Gas(0), is_terminating=False),
            58: OpCode(name="load_u64", fn=cls.load_u(64), gas=Gas(0), is_terminating=False),
            59: OpCode(name="store_u8", fn=cls.store_u(8), gas=Gas(0), is_terminating=False),
            60: OpCode(name="store_u16", fn=cls.store_u(16), gas=Gas(0), is_terminating=False),
            61: OpCode(name="store_u32", fn=cls.store_u(32), gas=Gas(0), is_terminating=False),
            62: OpCode(name="store_u64", fn=cls.store_u(64), gas=Gas(0), is_terminating=False),
        }

    def jump_ind(
        self, registers: Registers, memory: Memory
    ) -> OpReturn:
        status, counter = self.program.djump(self.counter, floor(int(registers[self.ra]) + self.vx) % 2**32)
        return status, counter, registers, memory 
            
    def load_imm(
        self, registers: Registers, memory: Memory
    ) -> OpReturn:
        """
        OPC20: Load a 64-bit immediate value into a register.
        """
        registers[self.ra] = Register(self.vx)
        print(f"LOAD: {int(registers[self.ra])} in Register({self.ra}) \nRegisters: {registers}")
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    @staticmethod
    def load_u(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def load_u_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            registers[self.ra] = Register(
                IntegerCodec.decode_from(
                    bitsize // 8, 
                    memory.read(self.vx, bitsize // 8)
                )[0]
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return load_u_impl
    
    @staticmethod
    def store_u(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def store_u_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            memory.write(self.vx, int(registers[self.ra]) % (2**bitsize))
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return store_u_impl
    
    @staticmethod
    def load_i(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def load_i_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            registers[self.ra] = Register(
                PvmUtilities.chi(
                    IntegerCodec.decode_from(bitsize // 8, memory.read(self.vx, bitsize // 8))[0],
                    bitsize // 8
                )
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return load_i_impl