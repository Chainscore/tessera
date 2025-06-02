from decimal import Decimal
from math import trunc
from typing import Any, Callable, Dict
from jam.execution.pvm.instructions.opcode import OpCode, OpReturn
from jam.execution.pvm.memory import Memory
from jam.execution.pvm.register import Registers
from jam.execution.pvm.status import CONTINUE
from jam.execution.pvm.utils import PvmUtilities
from jam.execution.pvm.instructions.instruction_table import InstructionTable
from jam.types.protocol.core import Gas, Register


class InstructionsWArgs3Reg(InstructionTable):

    @property
    def ra(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) % 16)

    @property
    def rb(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 1]) // 16)
    
    @property
    def rd(self) -> int:
        return min(12, int(self.program.zeta[self.counter + 2]))

    @classmethod
    def table(cls) -> Dict[int, OpCode]:
        return {
            190: OpCode(name="add_32", fn=cls.add_32, gas=Gas(1), is_terminating=False),
            191: OpCode(name="sub_32", fn=cls.sub_32, gas=Gas(1), is_terminating=False),
            192: OpCode(name="mul_32", fn=cls.mul_32, gas=Gas(1), is_terminating=False),
            193: OpCode(name="div_u_32", fn=cls.div_u_32, gas=Gas(1), is_terminating=False),
            194: OpCode(name="div_s_32", fn=cls.div_s_32, gas=Gas(1), is_terminating=False),
            195: OpCode(name="rem_u_32", fn=cls.rem_u_32, gas=Gas(1), is_terminating=False),
            196: OpCode(name="rem_s_32", fn=cls.rem_s_32, gas=Gas(1), is_terminating=False),
            197: OpCode(name="shlo_l_32", fn=cls.shlo_l_32, gas=Gas(1), is_terminating=False),
            198: OpCode(name="shlo_r_32", fn=cls.shlo_r_32, gas=Gas(1), is_terminating=False),
            199: OpCode(name="shar_r_32", fn=cls.shar_r_32, gas=Gas(1), is_terminating=False),
            200: OpCode(name="add_64", fn=cls.add_64, gas=Gas(1), is_terminating=False),
            201: OpCode(name="sub_64", fn=cls.sub_64, gas=Gas(1), is_terminating=False),
            202: OpCode(name="mul_64", fn=cls.mul_64, gas=Gas(1), is_terminating=False),
            203: OpCode(name="div_u_64", fn=cls.div_u_64, gas=Gas(1), is_terminating=False),
            204: OpCode(name="div_s_64", fn=cls.div_s_64, gas=Gas(1), is_terminating=False),
            205: OpCode(name="rem_u_64", fn=cls.rem_u_64, gas=Gas(1), is_terminating=False),
            206: OpCode(name="rem_s_64", fn=cls.rem_s_64, gas=Gas(1), is_terminating=False),
            207: OpCode(name="shlo_l_64", fn=cls.shlo_l_64, gas=Gas(1), is_terminating=False),
            208: OpCode(name="shlo_r_64", fn=cls.shlo_r_64, gas=Gas(1), is_terminating=False),
            209: OpCode(name="shar_r_64", fn=cls.shar_r_64, gas=Gas(1), is_terminating=False),
            210: OpCode(name="and", fn=cls._op("and"), gas=Gas(1), is_terminating=False),
            211: OpCode(name="xor", fn=cls._op("xor"), gas=Gas(1), is_terminating=False),
            212: OpCode(name="or", fn=cls._op("or"), gas=Gas(1), is_terminating=False),
            213: OpCode(name="mul_upper_s_s", fn=cls.mul_upper_s_s, gas=Gas(1), is_terminating=False),
            214: OpCode(name="mul_upper_u_u", fn=cls.mul_upper_u_u, gas=Gas(1), is_terminating=False),
            215: OpCode(name="mul_upper_s_u", fn=cls.mul_upper_s_u, gas=Gas(1), is_terminating=False),
            216: OpCode(name="set_lt_u", fn=cls.set_lt_u, gas=Gas(1), is_terminating=False),
            217: OpCode(name="set_lt_s", fn=cls.set_lt_s, gas=Gas(1), is_terminating=False),
            218: OpCode(name="cmov_iz", fn=cls.cmov_iz, gas=Gas(1), is_terminating=False),
            219: OpCode(name="cmov_nz", fn=cls.cmov_nz, gas=Gas(1), is_terminating=False),
            220: OpCode(name="rot_l_64", fn=cls.rot_l_64, gas=Gas(1), is_terminating=False),
            221: OpCode(name="rot_l_32", fn=cls.rot_l_32, gas=Gas(1), is_terminating=False),
            222: OpCode(name="rot_r_64", fn=cls.rot_r(64), gas=Gas(1), is_terminating=False),
            223: OpCode(name="rot_r_32", fn=cls.rot_r(32), gas=Gas(1), is_terminating=False),
            224: OpCode(name="and_inv", fn=cls._op("and", inv_b=True), gas=Gas(1), is_terminating=False),
            225: OpCode(name="or_inv", fn=cls._op("or", inv_b=True), gas=Gas(1), is_terminating=False),
            226: OpCode(name="xnor", fn=cls._op("xor", inv_res=True), gas=Gas(1), is_terminating=False),
            227: OpCode(name="max", fn=cls._max, gas=Gas(1), is_terminating=False),
            228: OpCode(name="max_u", fn=cls._max_u, gas=Gas(1), is_terminating=False),
            229: OpCode(name="min", fn=cls._min, gas=Gas(1), is_terminating=False),
            230: OpCode(name="min_u", fn=cls._min_u, gas=Gas(1), is_terminating=False),
        }

    def add_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.chi(
                (int(registers[self.ra]) + int(registers[self.rb])) % 2**32,
                4
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def add_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            (int(registers[self.ra]) + int(registers[self.rb])) % 2**64
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def sub_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.chi(
                (int(registers[self.ra]) + 2**32 - (int(registers[self.rb]) % 2**32)) % 2**32, 
                4
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def sub_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register((int(registers[self.ra]) + 2**64 - int(registers[self.rb])) % 2**64)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def mul_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.chi(
                (int(registers[self.ra]) * int(registers[self.rb])) % 2**32, 
                4
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def mul_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register((int(registers[self.ra]) * int(registers[self.rb])) % 2**64)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def div_u_32(self, registers: Registers, memory: Memory) -> OpReturn:
        if (registers[self.rb] % 2**32) == 0:
            value = 2**64 - 1
        else:
            value = PvmUtilities.chi((registers[self.ra] % 2**32) // (registers[self.rb] % 2**32), 4)

        registers[self.rd] = Register(value)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def div_u_64(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] == 0:
            value = 2**64 - 1
        else:
            value = trunc(Decimal(int(registers[self.ra])) / int(registers[self.rb]))

        registers[self.rd] = Register(value)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def div_s_32(self, registers: Registers, memory: Memory) -> OpReturn:
        a = PvmUtilities.z(registers[self.ra] % 2**32, 4)
        b = PvmUtilities.z(registers[self.rb] % 2**32, 4)
        if b == 0:
            value = 2**64 - 1
        elif a == -2**31 and b == -1:
            value = PvmUtilities.z_inv(a, 8)
        else:
            value = PvmUtilities.z_inv(trunc(a / b), 8)

        registers[self.rd] = Register(value)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def div_s_64(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] == 0:
            value = 2**64 - 1
        else:
            a = PvmUtilities.z(registers[self.ra], 8)
            b = PvmUtilities.z(registers[self.rb], 8)
            if a == -2**63 and b == -1:
                value = registers[self.ra]
            else:
                value = PvmUtilities.z_inv(trunc(Decimal(a) / b), 8)

        registers[self.rd] = Register(value)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rem_u_32(self, registers: Registers, memory: Memory) -> OpReturn:
        a = registers[self.ra] % 2**32
        b = registers[self.rb] % 2**32
        registers[self.rd] = Register(PvmUtilities.chi(a if b == 0 else a % b, 4) )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rem_u_64(self, registers: Registers, memory: Memory) -> OpReturn:
        a = registers[self.ra]
        b = registers[self.rb]
        registers[self.rd] = a if b == 0 else a % b
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rem_s_32(self, registers: Registers, memory: Memory) -> OpReturn:
        a = PvmUtilities.z(registers[self.ra] % 2**32, 4)
        b = PvmUtilities.z(registers[self.rb] % 2**32, 4)
        if a == -2**31 and b == -1:
            registers[self.rd] = Register(0)
        else: 
            registers[self.rd] = Register(PvmUtilities.z_inv(
                PvmUtilities.smod(a, b), 
                8
            ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rem_s_64(self, registers: Registers, memory: Memory) -> OpReturn:
        a = PvmUtilities.z(registers[self.ra], 8)
        b = PvmUtilities.z(registers[self.rb], 8)
        if a == -2**31 and b == -1:
            registers[self.rd] = Register(0)
        else: 
            registers[self.rd] = Register(PvmUtilities.z_inv(
                PvmUtilities.smod(a, b), 
                8
            ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def shlo_l_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(PvmUtilities.chi(
            (int(registers[self.ra]) * 2**(int(registers[self.rb]) % 32)) % 2**32,
            4
        ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def shlo_l_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register((int(registers[self.ra]) * 2**(int(registers[self.rb]) % 64)) % 2**64)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def shlo_r_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(PvmUtilities.chi(
            (registers[self.ra] % 2**32) // 2**(int(registers[self.rb]) % 32),
            4
        ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def shlo_r_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register((int(registers[self.ra]) % 2**64) // 2**(int(registers[self.rb]) % 64))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def shar_r_32(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(PvmUtilities.z_inv(
            PvmUtilities.z(registers[self.ra] % 2**32, 4) // 2**(int(registers[self.rb]) % 32),
            8
        ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def shar_r_64(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(PvmUtilities.z_inv(
            PvmUtilities.z(
                registers[self.ra] % 2**64, 
                8
            ) // 2**(int(registers[self.rb]) % 64),
            8
        ))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def _op(op: str, inv_a = False, inv_b = False, inv_res = False):
        def op_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            ba = PvmUtilities.b(registers[self.ra], 8)
            bb = PvmUtilities.b(registers[self.rb], 8)
            result = [0] * 64
            for i in range(64):
                a = (not ba[i]) if inv_a else ba[i]
                b = (not bb[i]) if inv_b else bb[i]
                result[i] = PvmUtilities.compare(a, b, op)
                if inv_res:
                    result[i] = (not result[i])
            registers[self.rd] = Register(PvmUtilities.b_inv(result))
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return op_impl
    
    def mul_upper_s_s(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.z_inv(
                PvmUtilities.z(registers[self.ra], 8) * PvmUtilities.z(registers[self.rb], 8) 
                // 2**64,
                8
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def mul_upper_u_u(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register((int(registers[self.ra]) * int(registers[self.rb])) // 2**64)
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def mul_upper_s_u(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.z_inv(
                PvmUtilities.z(int(registers[self.ra]), 8) * int(registers[self.rb])
                // 2**64,
                8
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def set_lt_u(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(int(registers[self.ra] < registers[self.rb]))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def set_lt_s(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(int(PvmUtilities.z(registers[self.ra], 8) < PvmUtilities.z(registers[self.rb], 8)))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def cmov_iz(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] == 0:
            registers[self.rd] = registers[self.ra] 
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def cmov_nz(self, registers: Registers, memory: Memory) -> OpReturn:
        if registers[self.rb] != 0:
            registers[self.rd] = registers[self.ra] 
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def _max(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.z_inv(
                max(PvmUtilities.z(registers[self.ra], 8), PvmUtilities.z(registers[self.rb], 8)),
                8
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def _max_u(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(max(registers[self.ra], registers[self.rb]))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def _min(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(
            PvmUtilities.z_inv(
                min(PvmUtilities.z(registers[self.ra], 8), PvmUtilities.z(registers[self.rb], 8)),
                8
            )
        )
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def _min_u(self, registers: Registers, memory: Memory) -> OpReturn:
        registers[self.rd] = Register(min(registers[self.ra], registers[self.rb]))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rot_l_64(self, registers: Registers, memory: Memory) -> OpReturn:
        x = [False] * 64
        ba = PvmUtilities.b(registers[self.ra], 8)
        for i in range(64):
            x[(i+int(registers[self.rb])) % 64] = ba[i]
        registers[self.rd] = Register(PvmUtilities.b_inv(x))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory

    def rot_l_32(self, registers: Registers, memory: Memory) -> OpReturn:
        x = [False] * 32
        ba = PvmUtilities.b(int(registers[self.ra]) % 2**32, 4)
        for i in range(32):
            x[(i+int(registers[self.rb])) % 32] = ba[i]
        registers[self.rd] = Register(PvmUtilities.chi(PvmUtilities.b_inv(x), 4))
        return CONTINUE, self.counter + self.skip_index + 1, registers, memory
    
    def rot_r(bitsize: int) -> Callable[[Any, Registers, Memory], OpReturn]:
        def rot_r_impl(self, registers: Registers, memory: Memory) -> OpReturn:
            a_bits = PvmUtilities.b(int(registers[self.ra]) % 2**(bitsize), bitsize // 8)
            b = int(registers[self.rb]) % 2**(bitsize)
            x = PvmUtilities.b_inv([a_bits[(i+b) % bitsize] for i in range(bitsize)])
            if bitsize < 64:
                x = PvmUtilities.chi(x, bitsize//8)
            registers[self.rd] = Register(x)
            return CONTINUE, self.counter + self.skip_index + 1, registers, memory
        return rot_r_impl