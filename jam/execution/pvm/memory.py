from math import ceil, floor
from typing import Dict, List, Self, Sequence
from jam.execution.pvm.types import Accessibility
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.utils.constants import PVM_INIT_DATA_SIZE, PVM_MEMORY_PAGE_SIZE, PVM_INIT_ZONE_SIZE



class Memory:
    """
    Memory is a class that models the memory of a program.
    """

    ADDR_MOD = 2 ** 32
    LOW_BOUND = 2 ** 16
    HEAP_START = 0x100000

    data: Dict[int, int]

    def __init__(self, data: Dict[int, int] = {}, allowed_read_pages=[], allowed_write_pages=[]):
        """
        Initialize the Memory structure.

        Args:
            allowed_read_pages (set): Set of page numbers allowed for read access.
            allowed_write_pages (set): Set of page numbers allowed for write access.
        """
        self.allowed_read_pages = allowed_read_pages
        self.allowed_write_pages = allowed_write_pages

        # Memory is modeled as a dictionary mapping an address to a byte (0-255).
        for addr, val in data.items():
            # Validate
            if not isinstance(addr, U32) or not isinstance(val, Byte) or val < 0 or val > 255:
                raise Exception(f"Memory: Invalid memory value at address {addr}: {val}. {not isinstance(addr, U32)} or {not isinstance(val, Byte)} or {val < 0} or {val > 255}")
        self.data = data

    def _check_address(self, addr: int, for_write=False):
        """
        Check if the given address is accessible.

        Raises an exception if the address is below the low bound or if its page is not allowed.
        """
        addr = floor(addr % self.ADDR_MOD)  # Ensure address is within 0..2^32-1.
        # Address cannot be below the low bound.
        if addr < self.LOW_BOUND:
            raise Exception(f"Memory Panic: Address {addr} is below the allowed threshold ({self.LOW_BOUND}).")
        # Address must be in a valid page.
        page = addr // PVM_MEMORY_PAGE_SIZE
        # If writing, the page must be allowed to be written.
        if for_write:
            if page not in self.allowed_write_pages:
                raise PvmError(PvmErrorCodes.PAGE_FAULT, f"Memory Fault: Write access denied for address {addr} (page {page}).", addr)
        # Else (reading), the page must be allowed to be write / read
        else:
            if (page not in self.allowed_read_pages) and (page not in self.allowed_write_pages):
                raise PvmError(PvmErrorCodes.PAGE_FAULT, f"Memory Fault: Read access denied for address {addr} (page {page}).", page)
        return addr

    def read(self, address: int, length: int) -> bytes:
        """
        Read a sequence of bytes starting from 'address' with given 'length'.

        Returns a list of integers (each 0-255).
        Unwritten addresses return 0 (default uninitialized value).
        """
        bytes_out = []
        for offset in range(length):
            addr = self._check_address((address + offset) % self.ADDR_MOD, for_write=False)
            # Return stored byte or 0 if the address has not been written.
            bytes_out.append(self.data.get(addr, Byte(0)))
        return bytes(Bytes(bytes_out))

    def write(self, address: int, data_bytes: bytes|Sequence[int]):
        """
        Write a sequence of bytes starting at 'address'.

        data_bytes should be an iterable of integers (each 0-255).
        """
        for offset, byte in enumerate(data_bytes):
            addr = self._check_address((address + offset) % self.ADDR_MOD, for_write=True)
            self.data[U32(addr)] = Byte(byte)

    def is_accessible(self, address: int, length: int, for_write = False) -> bool:
        pages = self.get_pages(address, address+length)
        for page in pages:
            if for_write and page not in self.allowed_write_pages:
                return False
            # Else (reading), the page must be allowed to be write / read
            elif (page not in self.allowed_read_pages) and (page not in self.allowed_write_pages):
                return False
        return True

    def dump_memory(self, start, end):
        """
        For debugging: return a list of byte values from address 'start' to 'end' (exclusive).
        """
        return [self.data.get(addr, 0) for addr in range(start, end)]

    def __repr__(self):
        return f"Memory(data={str(self.data)}, allowed_read_pages={str(self.allowed_read_pages)}, allowed_write_pages={str(self.allowed_write_pages)})"

    def __eq__(self, other):
        # Dont compare if zero
        data_eq = True
        for data in self.data:
            if self.data[data] != 0 and data in other.data:
                if self.data[data] != other.data[data]:
                    data_eq = False

        for data in other.data:
            if other.data[data] != 0 and data in self.data:
                if self.data[data] != other.data[data]:
                    data_eq = False

        return data_eq and self.allowed_read_pages == other.allowed_read_pages and self.allowed_write_pages == other.allowed_write_pages

    @classmethod
    def from_pc(cls, read: bytes, write: bytes, args: bytes, z: int, s: int) -> Self:
        memory = {}

        read_start = PVM_INIT_ZONE_SIZE
        read_pages = cls.get_pages(read_start, read_start + cls.total_page_size(len(read)))
        for i, byt in enumerate(read):
            memory[Byte(read_start+i)] = Byte(byt)

        write_start = 2*PVM_INIT_ZONE_SIZE + cls.total_zone_size(len(read))
        write_pages = cls.get_pages(write_start, write_start + cls.total_page_size(len(write)) + (z * PVM_MEMORY_PAGE_SIZE))
        for i, byt in enumerate(write):
            memory[U32(write_start+i)] = Byte(byt)

        write_pages.extend(
            cls.get_pages(
                2**32 - 2*PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE - cls.total_page_size(s),
                2**32 - 2*PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
            )
        )

        arg_start = 2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
        read_pages.extend(cls.get_pages(arg_start, 2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE + cls.total_page_size(len(args))))
        for i, byt in enumerate(args):
            memory[U32(arg_start+i)] = Byte(byt)

        return cls(memory, read_pages, write_pages)

    def total_page_size(blob_len: int) -> int:
        """
        P function from https://graypaper.fluffylabs.dev/#/cc517d7/2be0022bea02?v=0.6.5
        Args:
            - blob_len: len on data to be stored
        Returns:
            - total page length
        """
        return PVM_MEMORY_PAGE_SIZE*ceil(blob_len/PVM_MEMORY_PAGE_SIZE)

    def total_zone_size(blob_len: int):
        """
        Z function from https://graypaper.fluffylabs.dev/#/cc517d7/2be0022bea02?v=0.6.5
        Args:
            - blob_len: len on data to be stored
        Returns:
            - total zone length
        """
        return PVM_INIT_ZONE_SIZE*ceil(blob_len/PVM_INIT_ZONE_SIZE)

    def get_pages(start_index: int, end_index: int) -> List[int]:
        """
        Gives a list of page numbers that contains a specific indexed location in memory
        """
        start = floor(start_index/PVM_MEMORY_PAGE_SIZE)
        end = ceil(end_index/PVM_MEMORY_PAGE_SIZE)
        return [i for i in range(start, end)]

    def zero_memory_range(self, start_address: int, offset: int):
        """
        Zero out memory values from address 'start_address' to 'end_address'.

        Args:
            start_address (int): The starting address to zero out.
            end_address (int): The ending address (excluded) to zero out.
        """
        # Loop over the memory range and set the values to 0
        end_address=start_address+offset
        for addr in range(start_address, end_address):
            self.data[addr] = 0  # Set the memory value at the address to 0

    def alter_accessibility(self, start_address: int, offset: int,access_type:Accessibility):
        """
        Alter the Page accessibility type from 'start_address' to 'end_address'.

        Args:
            start_address (int): The starting address to change its accebility type.
            end_address (int): The ending address to alter the same.
        """
        end_address=start_address+offset
        if access_type==Accessibility.read:
            for addr in range(start_address, end_address):
                if addr in self.allowed_write_pages:
                    self.allowed_write_pages.remove(addr)
                # Just checking wether its already present on write
                if addr not in self.allowed_read_pages:
                    self.allowed_read_pages.append(addr)
        elif access_type==Accessibility.write:
            for addr in range(start_address, end_address):
                if addr in self.allowed_read_pages:
                    self.allowed_read_pages.remove(addr)
                # Just checking wether its already present on write
                if addr not in self.allowed_write_pages:
                    self.allowed_write_pages.append(addr)
        else :
            # Removing from all the allowed_read/write to make it Nullable Type
            for addr in range(start_address, end_address):
                if addr in self.allowed_read_pages:
                    self.allowed_read_pages.remove(addr)
                if addr in self.allowed_write_pages:
                    self.allowed_write_pages.remove(addr)
