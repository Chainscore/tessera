
from typing import List, Self, Tuple, Union, cast
from jam.types.base.bit import Bit
from jam.types.base.integers.fixed import U8
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec
from jam.utils.codec.utils import check_buffer_size

class Program(Codable):
    """This is the program blob which the PVM will execute.

    Args:
        z: Size of jump-table entries
        jump_table: sequence of NN, each of size z
        instruction_set: Sequence of instructions (U8)
        offset_bitmask: Bitsequence of size len(instruction_set) that defines which blob is an opcode

    """
    z: U8
    jump_table: List[int]
    instruction_set: List[U8]
    offset_bitmask: List[Bit]

    def __init__(self, _z, _jump_table, _instruction_set, _bit_mask):
        self.z = _z
        self.jump_table = _jump_table
        self.instruction_set = _instruction_set
        self.offset_bitmask = _bit_mask

    def encode_size(self) -> int:
        total_size = 0
        total_size += GeneralCodec().encode_size(len(self.jump_table))
        total_size += self.z.encode_size()
        total_size += GeneralCodec().encode_size(len(self.instruction_set))
        for jump in self.jump_table:
            total_size += IntegerCodec(self.z.value).encode_size(jump)
        for instruction in self.instruction_set:
            total_size += instruction.encode_size()
        total_size += BitSequenceCodec(len(self.instruction_set)).encode_size(self.offset_bitmask)
        return total_size

    def encode_into(self, buffer: Union[bytes, bytearray], offset: int = 0) -> int:
        """Encode the program bytecode into a buffer.

        Args:
            buffer: The buffer to encode the program into
            offset: Offset of the buffer to start encoding from
        """
        total_size = self.encode_size()
        check_buffer_size(buffer, total_size, offset)

        offset += GeneralCodec().encode_into(len(self.jump_table), buffer, offset)
        offset += self.z.encode_into(buffer, offset)
        offset += GeneralCodec().encode_into(len(self.instruction_set), buffer, offset)
        for jump in self.jump_table:
            offset += IntegerCodec(self.z.value).encode_into(jump, buffer, offset)
        for instruction in self.instruction_set:
            offset += instruction.encode_into(buffer, offset)
        offset += BitSequenceCodec(len(self.instruction_set), "lsb").encode_into(self.offset_bitmask, buffer, offset)

    @staticmethod
    def decode_from(buffer: Union[bytes, bytearray], offset: int = 0) -> Tuple[Self, int]:
        current_offset = offset
        bytes_read = 0

        j_len, size = GeneralCodec.decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        z, size = U8.decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        c_len, size = GeneralCodec.decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        j: List = []
        for _ in range(j_len):
            val, size = IntegerCodec.decode_from(z.value, buffer, current_offset)
            bytes_read +=  size
            current_offset += size
            j.append(val)
        
        c: List = []
        for _ in range(c_len):
            val, size = U8.decode_from(buffer, current_offset)
            bytes_read +=  size
            current_offset +=  size
            c.append(val)

        offset_bitmask, size = BitSequenceCodec.decode_from(buffer, current_offset, c_len, "lsb")
        bytes_read += size
        current_offset +=  size

        return Program(z, j, c, offset_bitmask), bytes_read
    
    @staticmethod
    def from_json(buffer: Union[bytes, bytearray]) -> Self:
        value, _ = Program.decode_from(buffer)
        return value
    
    def __repr__(self) -> str:
        return f"Program(z={self.z}, jump_table={self.jump_table}, instruction_set={self.instruction_set}, offset_bitmask={self.offset_bitmask})"



        

