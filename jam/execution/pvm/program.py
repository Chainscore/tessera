from math import floor
from typing import List, Tuple, Union
from tsrkit_types.itf.codable import Codable
from tsrkit_types.integers import Uint
from tsrkit_types.bits import Bits
from jam.execution.pvm.status import PvmError
from jam.execution.pvm.instructions.table_map import InstTableMap
from jam.execution.pvm.status import CONTINUE, HALT, PANIC, ExecutionStatus
from jam.execution.pvm.zeta import Zeta
from jam.utils.constants import PVM_ADDR_ALIGNMENT


class Program(Codable):
    """This is the program blob which the PVM will execute.

    Args:
        z: Size of jump-table entries
        jump_table: sequence of NN, each of size z
        instruction_set: Sequence of instructions (U8)
        offset_bitmask: Bitsequence of size len(instruction_set) that defines which blob is an opcode

    """

    z: int
    jump_table: List
    instruction_set: List[int]
    offset_bitmask: List
    basic_blocks: List

    def __init__(
        self,
        z: int,
        jump_table: List[int],
        instruction_set: List[int],
        offset_bitmask: List[bool],
    ):
        self.z = z
        self.jump_table = jump_table
        self.instruction_set = instruction_set
        self.offset_bitmask = offset_bitmask
        basic_blocks = [0]
        for n in range(len(self.instruction_set)):
            if (
                    self.offset_bitmask[n] and
                    self.instruction_set[n] in InstTableMap.terminating_blocks()
            ):
                basic_blocks.append(n + 1 + self.skip(n))
        self.basic_blocks = basic_blocks

    @property
    def zeta(self) -> Zeta:
        return Zeta(self.instruction_set)
    
    def skip(self, pc) -> int:
        """
        Skip the instructions until the next opcode is found.
        Args:
            pc: Current index
        Returns:
            Distance to the next opcode.
        """
        i = int(pc)
        extended_bitmask = self.offset_bitmask + [True] * (100)
        value = len(extended_bitmask)
        for j in range(i + 1, len(extended_bitmask)):
            if extended_bitmask[j] == 1:
                value = j - i - 1  # Distance to the next opcode.
                break
        return min(24, value) # Reached the end of the bitmask.

    def branch(
        self,
        counter: int,
        branch: int,
        condition: bool
    ) -> Tuple[ExecutionStatus, int]:
        if not condition:
            return CONTINUE, counter
        elif branch not in self.basic_blocks:
            raise PvmError(PANIC)
        return CONTINUE, branch

    def djump(
        self, 
        counter: int,
        a: int
    ) -> Tuple[ExecutionStatus, int]:
        if a == 2**32 - 2**16:
            return HALT, counter
        elif (
            a == 0 or
            a > (len(self.jump_table) * PVM_ADDR_ALIGNMENT) or
            a % PVM_ADDR_ALIGNMENT != 0 or
            self.jump_table[floor(a//PVM_ADDR_ALIGNMENT) - 1] not in self.basic_blocks
        ):
            raise PvmError(PANIC)
        return CONTINUE, self.jump_table[floor(a//PVM_ADDR_ALIGNMENT) - 1]

    def encode_size(self) -> int:
        """Encode the size of the program.

        Returns:
            int: Size of the program
        """
        total_size = 0
        total_size += Uint(len(self.jump_table)).encode_size()
        total_size += 1
        total_size += Uint(len(self.instruction_set)).encode_size()
        for jump in self.jump_table:
            total_size += Uint[self.z * 8](jump).encode_size()
        for instruction in self.instruction_set:
            total_size += instruction.encode_size()
        total_size += Bits[len(self.instruction_set)](self.offset_bitmask).encode_size()
        return total_size

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        """Encode the program bytecode into a buffer.

        Args:
            buffer: The buffer to encode the program into
            offset: Offset of the buffer to start encoding from
        """
        total_size = self.encode_size()
        self._check_buffer_size(buffer, total_size, offset)
        current_offset = offset
        size = Uint[8](len(self.jump_table)).encode_into(buffer, current_offset)
        current_offset += size
        size = Uint[8](self.z).encode_into(buffer, current_offset)
        current_offset += size
        size = Uint(len(self.instruction_set)).encode_into(
            buffer, current_offset
        )
        current_offset += size
        for jump in self.jump_table:
            size = Uint[self.z * 8](jump).encode_into(buffer, current_offset)
            current_offset += size
        for instruction in self.instruction_set:
            size = instruction.encode_into(buffer, current_offset)
            current_offset += size
        size = Bits[len(self.instruction_set), "lsb"](self.offset_bitmask).encode_into(
            buffer, current_offset
        )
        current_offset += size
        return current_offset - offset

    @classmethod
    def decode_from(
        cls, buffer: Union[bytes, bytearray], offset: int = 0
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

        j_len, size = Uint.decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        z, size = Uint[8].decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        c_len, size = Uint.decode_from(buffer, current_offset)
        bytes_read += size
        current_offset += size

        j: List = []
        for _ in range(j_len):
            val, size = Uint[z * 8].decode_from(buffer, current_offset)
            bytes_read += size
            current_offset += size
            j.append(val)

        c: List = []
        for _ in range(c_len):
            val, size = Uint[8].decode_from(buffer, current_offset)
            bytes_read += size
            current_offset += size
            c.append(val)

        offset_bitmask, size = Bits[c_len, "lsb"].decode_from(
            buffer, current_offset
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
