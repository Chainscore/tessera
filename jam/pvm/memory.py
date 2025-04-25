from math import floor
from typing import Dict, Sequence
from jam.pvm.errors import PvmError, PvmErrorCodes
from jam.types.base.integers.fixed import U32
from jam.types.base.sequences.bytes.bit_array import Byte
from jam.types.base.sequences.bytes.bytes import Bytes


class Memory:
    """
    Memory is a class that models the memory of a program.
    """

    PAGE_SIZE = 2**12
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
                raise Exception(f"Memory: Invalid memory value at address {addr}: {val}.")
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
        page = addr // self.PAGE_SIZE
        # If writing, the page must be allowed to be written.
        if for_write:
            if page not in self.allowed_write_pages:
                raise PvmError(PvmErrorCodes.PAGE_FAULT, f"Memory Fault: Write access denied for address {addr} (page {page}).", addr)
        # Else (reading), the page must be allowed to be read.
        else:
            if page not in self.allowed_read_pages:
                raise PvmError(PvmErrorCodes.PAGE_FAULT, f"Memory Fault: Read access denied for address {addr} (page {page}).", addr)
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
