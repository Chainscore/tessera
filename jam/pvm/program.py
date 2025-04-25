from math import floor
from typing import List, Self, Tuple, Union

from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.pvm.instructions.table_map import InstTableMap
from jam.pvm.status import CONTINUE, HALT, PANIC, ExecutionStatus
from jam.pvm.zeta import Zeta
from jam.types.base.integers.fixed import U8, U32
from jam.types.protocol.core import ProgramCounter
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.bit_sequences import BitSequenceCodec
from jam.utils.codec.primitives.integers import GeneralCodec, IntegerCodec
from jam.utils.codec.utils import check_buffer_size
from jam.utils.constants import PVM_ADDR_ALIGNMENT
from jam.utils.json.serde import JsonSerde


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
        offset_bitmask: List[bool],
    ):
        self.z = z
        self.jump_table = jump_table
        self.instruction_set = instruction_set
        self.offset_bitmask = offset_bitmask

    @property
    def zeta(self) -> Zeta:
        return Zeta(self.instruction_set)
    
    def skip(self, i) -> int:
        """
        Skip the instructions until the next opcode is found.
        Args:
            i: Current index
        Returns:
            Distance to the next opcode.
        """
        i = int(i)
        extended_bitmask = self.offset_bitmask + [True] * (100)
        value = len(extended_bitmask)
        for j in range(i + 1, len(extended_bitmask)):
            if extended_bitmask[j] == 1:
                value = j - i - 1  # Distance to the next opcode.
                break
        return min(24, value) # Reached the end of the bitmask.

    @property
    def basic_blocks(self) -> List[int]:
        """Get the basic blocks of the program. ie. sequences of instructions
        where the code sequence starts.

        Returns:
            List[U8]: List of basic blocks
        """
        basic_blocks = [0]
        for n in range(len(self.instruction_set)):
            if (
                self.offset_bitmask[n] and 
                self.instruction_set[n].value in InstTableMap.terminating_blocks()
            ):
                basic_blocks.append(n + 1 + self.skip(n))
        return basic_blocks
    
    def branch(
        self,
        counter: ProgramCounter, 
        branch: ProgramCounter, 
        condition: bool
    ) -> Tuple[ExecutionStatus, ProgramCounter]:
        if not condition:
            return CONTINUE, counter
        elif branch not in self.basic_blocks:
            raise PvmError(PvmErrorCodes.PANIC)
        print("JUMP:", branch)
        return CONTINUE, branch

    def djump(
        self, 
        counter: ProgramCounter, 
        a: int
    ) -> Tuple[ExecutionStatus, ProgramCounter]:
        print(f"djumping {a}")
        if a == 2**32 - 2**16:
            return HALT, counter
        elif (
            a == 0 or
            a > (len(self.jump_table) * PVM_ADDR_ALIGNMENT) or
            a % PVM_ADDR_ALIGNMENT != 0 or
            self.jump_table[floor(a//PVM_ADDR_ALIGNMENT) - 1] not in self.basic_blocks
        ):
            print(f"Either of {a == 0} or {a > (len(self.jump_table) * PVM_ADDR_ALIGNMENT)} or {a % PVM_ADDR_ALIGNMENT != 0}")
            raise PvmError(PvmErrorCodes.PANIC)
        return CONTINUE, self.jump_table[floor(a//PVM_ADDR_ALIGNMENT) - 1]
    
    def encode_size(self) -> int:
        """Encode the size of the program.

        Returns:
            int: Size of the program
        """
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

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
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
    ) -> Tuple["Program", int]:
        """Decode a program from a bytes

        Args:
            buffer (Union[bytes, bytearray]): Bytes
            offset (int, optional): Where to start decoding from. Defaults to 0.

        Returns:
            Tuple[Self, int]: Returns Program and bytes read

        TODO: Implement conditions - https://graypaper.fluffylabs.dev/#/68eaa1f/234701234701?v=0.6.4
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

        return Program(z, j, c, list(offset_bitmask)), bytes_read

    @classmethod
    def from_json(cls, data: Union[bytes, bytearray]) -> "Program":
        """Decode a program from a bytes

        Args:
            buffer (Union[bytes, bytearray]): Bytes

        Returns:
            Tuple[Self, int]: Returns Program and bytes read
        """
        value, _ = Program.decode_from(data)
        return value

    def __repr__(self):
        return f"Program(z={self.z}, jump_table={self.jump_table}, instruction_set={self.instruction_set}, offset_bitmask={self.offset_bitmask})"
    
    def __eq__(self, other):
        return self.z == other.z and self.jump_table == other.jump_table and self.instruction_set == other.instruction_set and self.offset_bitmask == other.offset_bitmask
