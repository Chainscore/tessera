from math import ceil, floor
from typing import Dict, List, Self, Sequence

from jam.config.logging import logger
from jam.execution.pvm.types import Accessibility
from jam.execution.pvm.status import PvmError, PAGE_FAULT
from jam.utils.constants import PVM_INIT_DATA_SIZE, PVM_MEMORY_PAGE_SIZE, PVM_INIT_ZONE_SIZE


class Memory:
    """
    Memory is a class that models the memory of a program.
    """

    ADDR_MOD = 2 ** 32
    LOW_BOUND = 0

    heap_break = 0

    data: Dict[int, int]

    def __init__(self, data: Dict[int, int] = {}, allowed_read_pages=[], allowed_write_pages=[], heap = 0):
        """
        Initialize the Memory structure.

        Args:
            allowed_read_pages (list): Set of page numbers allowed for read access.
            allowed_write_pages (list): Set of page numbers allowed for write access.
        """
        self.allowed_read_pages = allowed_read_pages
        self.allowed_write_pages = allowed_write_pages

        # Memory is modeled as a dictionary mapping an address to a byte (0-255).
        for addr, val in data.items():
            # Validate
            if not isinstance(addr, int) or not isinstance(val, int) or val < 0 or val > 255:
                raise Exception(f"Memory: Invalid memory value at address {addr}: {val}")

        self.data = data

        self.heap_break = heap

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
                logger.debug(f"Not allowed to write {addr}(Page={page})")
                raise PvmError(PAGE_FAULT(addr))
        # Else (reading), the page must be allowed to be write / read
        else:
            if (page not in self.allowed_read_pages) and (page not in self.allowed_write_pages):
                logger.debugc(f"Not allowed to read {addr}(Page={page})")
                raise PvmError(PAGE_FAULT(addr))
        return addr

    def read(self, address: int, length: int) -> bytes:
        """
        Read a sequence of bytes starting from 'address' with given 'length'.

        Returns a list of integers (each 0-255).
        Unwritten addresses return 0 (default uninitialized value).
        """
        if length == 0:
            return bytes(0)
        bytes_out = []
        for offset in range(length):
            addr = self._check_address((address + offset) % self.ADDR_MOD, for_write=False)
            # Return stored byte or 0 if the address has not been written.
            bytes_out.append(self.data.get(addr, 0))

        # print(f"u{length*8}[{Bytes(address)}] ({Bytes(bytes_out)})")
        return bytes(bytes_out)

    def write(self, address: int, data_bytes: bytes|Sequence[int]):
        """
        Write a sequence of bytes starting at 'address'.

        data_bytes should be an iterable of integers (each 0-255).
        """
        if len(data_bytes) == 0:
            return
        address = int(address)
        # print(f"u{len(data_bytes) * 8}[{(int(address) % self.ADDR_MOD).to_bytes(4).hex()}]({self.read(int(address) % self.ADDR_MOD, len(data_bytes)).hex()}) = {bytes(data_bytes).hex()}")
        for offset, byte in enumerate(data_bytes):
            addr = self._check_address((address + offset) % self.ADDR_MOD, for_write=True)
            self.data[addr] = int(byte)

    def is_accessible(self, address: int, length: int, for_write = False) -> bool:
        if length == 0:
            return True
        pages = self.get_pages(address, length)
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
        read_pages = cls.get_pages(read_start, cls.total_page_size(len(read)))
        print(f"READ \t\t | Start: {int(read_start).to_bytes(4).hex()} \t | End {int(read_pages[-1] * PVM_MEMORY_PAGE_SIZE).to_bytes(4).hex()}")
        for i, byt in enumerate(read):
            memory[read_start+i] = int(byt)

        write_start = 2*PVM_INIT_ZONE_SIZE + cls.total_zone_size(len(read))
        write_pages = cls.get_pages(write_start, cls.total_page_size(len(write)) + (z * PVM_MEMORY_PAGE_SIZE))
        print(f"WRITE \t\t | Start: {int(write_start).to_bytes(4).hex()} \t | End {int((write_pages[-1] + 1) * PVM_MEMORY_PAGE_SIZE).to_bytes(4).hex()}")
        for i, byt in enumerate(write):
            memory[write_start+i] = int(byt)

        heap = int((write_pages[-1] + 1) * PVM_MEMORY_PAGE_SIZE)

        write_pages.extend(
            cls.get_pages(
                2**32 - 2*PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE - cls.total_page_size(s),
                cls.total_page_size(s)
            )
        )

        arg_start = 2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
        read_pages.extend(cls.get_pages(arg_start, cls.total_page_size(len(args))))
        print(f"ARG \t\t | START: {int(arg_start).to_bytes(4).hex()}")
        for i, byt in enumerate(args):
            memory[arg_start+i] = int(byt)

        return cls(memory, read_pages, write_pages, heap=heap)

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

    @staticmethod
    def get_pages(start_index: int, length: int) -> List[int]:
        """
        Gives a list of page numbers that contains a specific indexed location in memory
        """
        start = floor(start_index/PVM_MEMORY_PAGE_SIZE)
        length = max(length, 1)
        end_index = start_index + length
        end = ceil(end_index/PVM_MEMORY_PAGE_SIZE)
        return [i for i in range(start, end+1)]

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

    def alter_accessibility(self, start_address: int, length: int, access_type: Accessibility):
        """
        Alter the Page accessibility type from 'start_address' to 'end_address'.

        Args:
            start_address (int): The starting address to change its accebility type.
            end_address (int): The ending address to alter the same.
        """
        pages = self.get_pages(start_address, length)
        for pg in pages:
            if access_type == Accessibility.WRITE:
                self.allowed_write_pages.append(pg)
            else:
                self.allowed_read_pages.append(pg)
