from typing import Any, Callable, Dict
from jam.pvm.instructions.opcode import OpCode, OpReturn
from jam.pvm.memory import Memory
from jam.pvm.register import Registers
from jam.pvm.status import CONTINUE
from jam.pvm.utils import PvmUtilities
from jam.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.primitives.integers import IntegerCodec

class InstructionsWArgs2Reg1Imm(InstructionTable):
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
            120: OpCode(name="store_ind_u8",        fn=cls.store_ind(8),            gas=Gas(1),         is_terminating=False),
            121: OpCode(name="store_ind_u16",       fn=cls.store_ind(16),           gas=Gas(1),         is_terminating=False),
            122: OpCode(name="store_ind_u32",       fn=cls.store_ind(32),           gas=Gas(1),         is_terminating=False),
            123: OpCode(name="store_ind_u64",       fn=cls.store_ind(64),           gas=Gas(1),         is_terminating=False),
            124: OpCode(name="load_ind_u8",         fn=cls.load_ind(8),             gas=Gas(1),         is_terminating=False),
            125: OpCode(name="load_ind_i8",         fn=cls.load_ind(8, True),       gas=Gas(1),         is_terminating=False),
            126: OpCode(name="load_ind_u16",        fn=cls.load_ind(16),            gas=Gas(1),         is_terminating=False),
            127: OpCode(name="load_ind_i16",        fn=cls.load_ind(16, True),      gas=Gas(1),     is_terminating=False),
            128: OpCode(name="load_ind_u32",        fn=cls.load_ind(32),            gas=Gas(1),         is_terminating=False),
            129: OpCode(name="load_ind_i32",        fn=cls.load_ind(32, True),      gas=Gas(1),     is_terminating=False),
            130: OpCode(name="load_ind_u64",        fn=cls.load_ind(64),            gas=Gas(1),         is_terminating=False),
            131: OpCode(name="add_imm_32",          fn=cls.add_imm(32),             gas=Gas(1),         is_terminating=False),
            132: OpCode(name="and_imm",             fn=cls.op_imm("and"),           gas=Gas(1),         is_terminating=False),
            133: OpCode(name="xor_imm",             fn=cls.op_imm("xor"),           gas=Gas(1),         is_terminating=False),
            134: OpCode(name="or_imm",              fn=cls.op_imm("or"),            gas=Gas(1),         is_terminating=False),
            135: OpCode(name="mul_imm_32",          fn=cls.mul_imm(32),             gas=Gas(1),         is_terminating=False),
            136: OpCode(name="set_lt_u_imm",        fn=cls.set_lt_u_imm,            gas=Gas(1),         is_terminating=False),
            137: OpCode(name="set_lt_s_imm",        fn=cls.set_lt_s_imm,            gas=Gas(1),         is_terminating=False),
            138: OpCode(name="shlo_l_imm_32",       fn=cls.shlo_l_imm(32),          gas=Gas(1),     is_terminating=False),
            139: OpCode(name="shlo_r_imm_32",       fn=cls.shlo_r_imm(32),          gas=Gas(1),     is_terminating=False),
            140: OpCode(name="shar_r_imm_32",       fn=cls.shar_r_imm(32),          gas=Gas(1),     is_terminating=False),
            141: OpCode(name="neg_add_imm_32",      fn=cls.neg_add_imm(32),         gas=Gas(1),         is_terminating=False),
            142: OpCode(name="set_gt_u_imm",        fn=cls.set_gt_u_imm,            gas=Gas(1),         is_terminating=False),
            143: OpCode(name="set_gt_s_imm",        fn=cls.set_gt_s_imm,            gas=Gas(1),         is_terminating=False),
            144: OpCode(name="shlo_l_imm_alt_32",   fn=cls.shlo_l_imm(32, True),    gas=Gas(1),         is_terminating=False),
            145: OpCode(name="shlo_r_imm_alt_32",   fn=cls.shlo_r_imm(32, True),    gas=Gas(1),         is_terminating=False),
            146: OpCode(name="shar_r_imm_alt_32",   fn=cls.shar_r_imm(32, True),    gas=Gas(1),         is_terminating=False),
            147: OpCode(name="cmov_iz_imm",         fn=cls.cmov_iz_imm,             gas=Gas(1),         is_terminating=False),
            148: OpCode(name="cmov_nz_imm",         fn=cls.cmov_nz_imm,             gas=Gas(1),         is_terminating=False),
            149: OpCode(name="add_imm_64",          fn=cls.add_imm(64),             gas=Gas(1),         is_terminating=False),
            150: OpCode(name="mul_imm_64",          fn=cls.mul_imm(64),             gas=Gas(1),         is_terminating=False),
            151: OpCode(name="shlo_l_imm_64",       fn=cls.shlo_l_imm(64),          gas=Gas(1),     is_terminating=False),
            152: OpCode(name="shlo_r_imm_64",       fn=cls.shlo_r_imm(64),          gas=Gas(1),     is_terminating=False),
            153: OpCode(name="shar_r_imm_64",       fn=cls.shar_r_imm(64),          gas=Gas(1),     is_terminating=False),
            154: OpCode(name="neg_add_imm_64",      fn=cls.neg_add_imm(64),         gas=Gas(1),         is_terminating=False),
            155: OpCode(name="shlo_l_imm_alt_64",   fn=cls.shlo_l_imm(64, True),    gas=Gas(1),         is_terminating=False),
            156: OpCode(name="shlo_r_imm_alt_64",   fn=cls.shlo_r_imm(64, True),    gas=Gas(1),         is_terminating=False),
            157: OpCode(name="shar_r_imm_alt_64",   fn=cls.shar_r_imm(64, True),    gas=Gas(1),         is_terminating=False),
            158: OpCode(name="rot_r_64_imm",        fn=cls.rot_imm(64),             gas=Gas(1),         is_terminating=False),
            159: OpCode(name="rot_r_64_imm_alt",    fn=cls.rot_imm(64, True),       gas=Gas(1),         is_terminating=False),
            160: OpCode(name="rot_r_32_imm",        fn=cls.rot_imm(32),             gas=Gas(1),         is_terminating=False),
            161: OpCode(name="rot_r_32_imm_alt",    fn=cls.rot_imm(32, True),       gas=Gas(1),         is_terminating=False),
        }

    def op_imm(op: str) -> Callable[[Any, Registers, Memory], OpReturn]:
        def op_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            wb_bits = PvmUtilities.b(registers[self.rb], 8)
            vx_bits = PvmUtilities.b(self.vx, 8)
            registers[self.ra] = Register(
                PvmUtilities.b_inv(
                    [PvmUtilities.compare(wb_bits[i], vx_bits[i], op) for i in range(64)]
                )
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return op_imm_impl

    def set_lt_u_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = Register(int(registers[self.rb] < self.vx))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def set_lt_s_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = Register(int(PvmUtilities.z(registers[self.rb], 8) < PvmUtilities.z(self.vx, 8)))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def shlo_l_imm(bitsize: int, alt = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def shlo_l_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            a = int(registers[self.rb]) if not alt else self.vx
            b = self.vx if not alt else int(registers[self.rb])

            registers[self.ra] = Register(
                PvmUtilities.chi(
                    (a * 2**(b % bitsize)) % 2**bitsize, 
                    bitsize // 8
                )
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return shlo_l_imm_impl
    
    def shlo_r_imm(bitsize: int, alt = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def shlo_r_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            a = int(registers[self.rb]) if not alt else self.vx
            b = self.vx if not alt else int(registers[self.rb])
                
            registers[self.ra] = Register(
                PvmUtilities.chi(
                    ((a % 2**(bitsize)) // 2**(b % bitsize)) % 2**(bitsize), 
                    bitsize // 8
                )
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return shlo_r_imm_impl
    
    def shar_r_imm(bitsize: int, alt = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def shar_r_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            a = int(registers[self.rb]) if not alt else self.vx
            b = self.vx if not alt else int(registers[self.rb])
                
            registers[self.ra] = Register(
                PvmUtilities.z_inv(
                    PvmUtilities.z(a % 2**(bitsize), bitsize // 8) // 2**(b % bitsize),
                    8
                )
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return shar_r_imm_impl
    
    def neg_add_imm(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def neg_add_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            value = (self.vx + 2**bitsize - int(registers[self.rb])) % 2**bitsize
            if bitsize < 64:
                value = PvmUtilities.chi(value, 4)
            registers[self.ra] = Register(value)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return neg_add_imm_impl
    

    def add_imm(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def add_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            value = (int(registers[self.rb]) + self.vx) % 2**(bitsize)
            if bitsize < 64:
                value = PvmUtilities.chi(value, bitsize // 8)
            registers[self.ra] = Register(value)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return add_imm_impl
    
    def mul_imm(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def mul_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            value = (registers[self.rb] * self.vx) % 2**(bitsize)
            if bitsize < 64:
                value = PvmUtilities.chi(value, 4)
            registers[self.ra] = Register(value)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return mul_imm_impl
    
    def rot_imm(bitsize: int, alt = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def rot_imm_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            a = int(registers[self.rb] if not alt else self.vx) % 2**(bitsize)
            b = int(self.vx if not alt else registers[self.rb]) % 2**(bitsize)

            a_bits = PvmUtilities.b(a, bitsize // 8)
            x = PvmUtilities.b_inv([a_bits[(i+b) % bitsize] for i in range(bitsize)])

            if bitsize < 64:
                x = PvmUtilities.chi(x, bitsize//8)
            
            registers[self.ra] = Register(x)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return rot_imm_impl
    
    def set_gt_u_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = Register(int(registers[self.rb] > self.vx))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def set_gt_s_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.ra] = Register(int(PvmUtilities.z(registers[self.rb], 8) > PvmUtilities.z(self.vx, 8)))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def cmov_iz_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] == 0:
            registers[self.ra] = Register(self.vx)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def cmov_nz_imm(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] != 0:
            registers[self.ra] = self.vx
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    @staticmethod
    def store_ind(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def store_ind_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            memory.write(
                int(registers[self.rb]) + self.vx,
                IntegerCodec(bitsize // 8).encode(int(registers[self.ra] % 2**bitsize))
            )
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return store_ind_impl
    
    @staticmethod
    def load_ind(bitsize: int, signed = False) -> Callable[[Any, Registers, Memory], OpReturn]:
        def load_ind_impl(
                self, registers: Registers, memory: Memory
        ) -> OpReturn:
            value = IntegerCodec.decode_from(
                bitsize // 8, 
                memory.read(int(registers[self.rb]) + self.vx, bitsize // 8)
            )[0]
            if signed:
                value = PvmUtilities.z_inv(PvmUtilities.z(value, bitsize // 8), 8)
            registers[self.ra] = Register(value)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return load_ind_impl