from dataclasses import dataclass
from typing import Self

from jam.execution.pvm.memory import Memory
from jam.execution.pvm.pvm import PVM
from jam.execution.pvm.register import Registers
from jam.types.protocol.core import Gas, ProgramCounter
from jam.utils.codec.codable import Codable
from jam.utils.codec.primitives.integers import IntegerCodec


@dataclass
class Code(Codable):
    read: bytes
    r_write: bytes
    code: bytes 
    z: int 
    s: int
    args: bytes

    @property
    def memory(self) -> Memory:
        return Memory.from_pc(self.read, self.r_write, self.args, self.z, self.s)
    
    @property
    def registers(self) -> Registers:
        return Registers.from_pc(self.args)
    
    def execute(self, gas: Gas, pc = ProgramCounter(0)):
        # status, pc, remaining_gas, registers, memory
        return PVM.execute(blob=self.code, program_counter=pc, gas=gas, registers=self.registers, memory=self.memory)
        
    @classmethod
    def decode_from(cls, pc: bytes) -> None|"Self":
        try:
            offset = 0
            o_len, decoded = IntegerCodec.decode_from(3, pc, offset)
            offset += decoded
            w_len, decoded = IntegerCodec.decode_from(3, pc, offset)
            offset += decoded
            z, decoded = IntegerCodec.decode_from(2, pc, offset)
            offset += decoded
            s, decoded = IntegerCodec.decode_from(3, pc, offset)
            offset += decoded
            # `o` (read-only data)
            o = pc[offset:offset+o_len]
            offset += o_len
            # `w` (read-write data)
            w = pc[offset:offset+w_len]
            offset += w_len
            # Code blobs
            c_len, decoded = IntegerCodec.decode_from(4, pc, offset)
            offset += decoded
            c = pc[offset:offset+c_len]
            offset += c_len
            # Arguments
            a = pc[offset:]
            return cls(read=o, r_write=w, z=z, s=s, code=c, args=a)
        except Exception:
            return None
    
    def encode_size(self):
        return 3+3+2+3+len(self.read)+len(self.r_write)+4+len(self.code)+len(self.args)
    
    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        start = offset
        
        offset += IntegerCodec(3).encode_into(len(self.read), buffer, offset)
        
        offset += IntegerCodec(3).encode_into(len(self.r_write), buffer, offset)
        
        offset += IntegerCodec(2).encode_into(self.z, buffer, offset)
        
        offset += IntegerCodec(3).encode_into(self.s, buffer, offset)
        
        buffer[offset: offset + len(self.read)] = self.read
        offset += len(self.read)
        
        buffer[offset: offset + len(self.r_write)] = self.r_write
        offset += len(self.r_write)
        
        offset += IntegerCodec(4).encode_into(len(self.code), buffer, offset)
        
        buffer[offset: offset + len(self.code)] = self.code
        offset += len(self.code)

        buffer[offset: offset + len(self.args)] = self.args
        offset += len(self.args)
        return offset - start
