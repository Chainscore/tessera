from typing import Any, Callable, Dict
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.code import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE, PANIC
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec

def compare(a: int, b: int, op: str) -> bool:
    return getattr(a, f"__{op}__")(b)

class InstructionsWArgs1Reg2Imm(InstructionTable):
    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def rb(self) -> int:
        return min(12, self.program.zeta[self.counter + 1] // 16)
    
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
            120: OpCode(name="store_ind_u8", fn=cls.store_ind(8), gas=Gas(0), is_terminating=False),
            121: OpCode(name="store_ind_u16", fn=cls.store_ind(16), gas=Gas(0), is_terminating=False),
            122: OpCode(name="store_ind_u32", fn=cls.store_ind(32), gas=Gas(0), is_terminating=False),
            123: OpCode(name="store_ind_u64", fn=cls.store_ind(64), gas=Gas(0), is_terminating=False),
            124: OpCode(name="load_ind_u8", fn=cls.load_ind(8), gas=Gas(0), is_terminating=False),
            125: OpCode(name="load_ind_i8", fn=cls.load_ind(8, True), gas=Gas(0), is_terminating=False),
            126: OpCode(name="load_ind_u16", fn=cls.load_ind(16), gas=Gas(0), is_terminating=False),
            127: OpCode(name="load_ind_i16", fn=cls.load_ind(16, True), gas=Gas(0), is_terminating=False),
            128: OpCode(name="load_ind_u32", fn=cls.load_ind(32), gas=Gas(0), is_terminating=False),
            129: OpCode(name="load_ind_i32", fn=cls.load_ind(32, True), gas=Gas(0), is_terminating=False),
            130: OpCode(name="load_ind_u64", fn=cls.load_ind(64), gas=Gas(0), is_terminating=False),
            131: OpCode(name="add_imm_32", fn=cls.add_imm_32, gas=Gas(0), is_terminating=False),
            132: OpCode(name="and_imm", fn=cls.op_imm("and"), gas=Gas(0), is_terminating=False),
            133: OpCode(name="xor_imm", fn=cls.op_imm("xor"), gas=Gas(0), is_terminating=False),
            134: OpCode(name="or_imm", fn=cls.op_imm("or"), gas=Gas(0), is_terminating=False),
        }

    def add_imm_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = PvmUtilities.chi((registers[self.rb] +  self.vx) % 2**32, 4)
        return CONTINUE, self.skip_index, registers, memory

    def op_imm(op: str) -> Callable[[Any, Registers, Memory], OpReturn]:
        def op_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            wb_bits = PvmUtilities.b(registers[self.rb], 8)
            vx_bits = PvmUtilities.b(registers[self.vx], 8)
            registers[self.ra] = Register(
                int.from_bytes(
                    PvmUtilities.b_inv(
                        [PvmUtilities.compare(wb_bits[i], vx_bits[i], op) for i in range(64)]
                    )
                )
            )
            return CONTINUE, self.skip_index, registers, memory
        return op_imm_impl

    def mul_imm_32(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory


    def set_lt_u_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory

    def set_lt_s_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory

    def add_imm_32(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory


    def add_imm_32(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory


    def add_imm_32(self, registers: Registers, memory: Memory) -> OpReturn:
        return CONTINUE, self.skip_index, registers, memory

    @staticmethod
    def store_ind(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def store_ind_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            memory.write(
                registers[self.rb] + self.vx,
                IntegerCodec(bitsize // 8).encode(registers[self.ra] % 2**bitsize)
            )
            return CONTINUE, self.skip_index, registers, memory
        return store_ind_impl
    
    @staticmethod
    def load_ind(bitsize: int, signed = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def load_ind_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            value = IntegerCodec.decode_from(
                bitsize // 8, 
                memory.get(registers[self.rb] + self.vx, bitsize // 8)
            )
            if signed:
                value = PvmUtilities.z_inv(PvmUtilities.z(value, bitsize // 8), 8)
            registers[self.ra] = value
            return CONTINUE, self.skip_index, registers, memory
        return load_ind_impl
    
    def add_imm