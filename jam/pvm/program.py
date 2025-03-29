from typing import List, Self, Tuple, Union
from jam.pvm.memory import MemoryChunk
from jam.pvm.pvm_memory import PageMemory
from jam.pvm.register import Registers
from jam.types.base.bit import Bit
from jam.types.base.integers.fixed import U8, U32
from jam.types.protocol.core import Gas, Register
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec
from jam.utils.codec.utils import check_buffer_size
from jam.utils.json.serde import JsonSerde
from jam.pvm.page_map import PageMap
from jam.pvm.extract import Execution


class Program(Codable, JsonSerde):
    """This is the program blob which the PVM will execute.

    Args:
        z: Size of jump-table entries
        jump_table: sequence of NN, each of size z
        instruction_set: Sequence of instructions (U8)
        offset_bitmask: Bitsequence of size len(instruction_set) that defines which blob is an opcode

    """

    z: U8
    jump_table: List
    instruction_set: List
    offset_bitmask: List

    def __init__(
        self,
        z: U8,
        jump_table: List[int],
        instruction_set: List[U8],
        offset_bitmask: List[Bit],
    ):
        self.z = z
        self.jump_table = jump_table
        self.instruction_set = instruction_set
        self.offset_bitmask = offset_bitmask

    def encode_size(self) -> int:
        total_size = 0
        total_size += GeneralCodec().encode_size(len(self.jump_table))
        total_size += self.z.encode_size()
        total_size += GeneralCodec().encode_size(len(self.instruction_set))
        for jump in self.jump_table:
            total_size += IntegerCodec(self.z.value).encode_size(jump)
        for instruction in self.instruction_set:
            total_size += instruction.encode_size()
        total_size += BitSequenceCodec(len(self.instruction_set)).encode_size(
            self.offset_bitmask
        )
        return total_size

    def encode_into(self, buffer: Union[bytes, bytearray], offset: int = 0) -> int:
        """Encode the program bytecode into a buffer.

        Args:
            buffer: The buffer to encode the program into
            offset: Offset of the buffer to start encoding from
        """
        total_size = self.encode_size()
        check_buffer_size(buffer, total_size, offset)
        current_offset = offset
        size = GeneralCodec().encode_into(len(self.jump_table), buffer, current_offset)
        current_offset += size
        size = self.z.encode_into(buffer, current_offset)
        current_offset += size
        size = GeneralCodec().encode_into(
            len(self.instruction_set), buffer, current_offset
        )
        current_offset += size
        for jump in self.jump_table:
            size = IntegerCodec(self.z.value).encode_into(jump, buffer, current_offset)
            current_offset += size
        for instruction in self.instruction_set:
            size = instruction.encode_into(buffer, current_offset)
            current_offset += size
        size = BitSequenceCodec(len(self.instruction_set), "lsb").encode_into(
            self.offset_bitmask, buffer, current_offset
        )
        current_offset += size
        return current_offset - offset

    @staticmethod
    def decode_from(
        buffer: Union[bytes, bytearray], offset: int = 0
    ) -> Tuple[Self, int]:
        """Decode a program from a bytes

        Args:
            buffer (Union[bytes, bytearray]): Bytes
            offset (int, optional): Where to start decoding from. Defaults to 0.

        Returns:
            Tuple[Self, int]: Returns Program and bytes read
        """
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
            bytes_read += size
            current_offset += size
            j.append(val)

        c: List = []
        for _ in range(c_len):
            val, size = U8.decode_from(buffer, current_offset)
            bytes_read += size
            current_offset += size
            c.append(val)

        offset_bitmask, size = BitSequenceCodec.decode_from(
            buffer, current_offset, c_len, "lsb"
        )
        bytes_read += size
        current_offset += size

        return Program(z, j, c, offset_bitmask), bytes_read

    @staticmethod
    def from_json(buffer: Union[bytes, bytearray]) -> Self:
        value, _ = Program.decode_from(buffer)
        return value

    def execute(
            self,
            initial_registers: Registers,
            gas: U32,
            memory: PageMemory,
            pc: U32,
    ) -> (Registers, MemoryChunk, U32):
        # TODO: Implement execute
        pvm_execution = Execution(pc, gas, initial_registers, memory, program=self)
        res = pvm_execution.process_program()
        return res
