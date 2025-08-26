from math import ceil
from typing import Dict, List, Sequence, Self

from jam.logging import logger
from jam.execution.pvm.types import Accessibility
from jam.execution.pvm.status import PvmError, PAGE_FAULT
from jam.utils.constants import (
    PVM_INIT_DATA_SIZE,
    PVM_MEMORY_PAGE_SIZE,
    PVM_INIT_ZONE_SIZE,
)

ADDR_MOD = 2**32
PAGE_SIZE = PVM_MEMORY_PAGE_SIZE
LOW_BOUND = 0


class Memory:
    """
    Sparse, page-mapped memory model with read/write page protection.
    """

    def __init__(
        self,
        data: Dict[int, int] | None = None,
        allowed_read_pages: List[int] | None = None,
        allowed_write_pages: List[int] | None = None,
        heap: int = 0,
    ):
        allowed_read_pages = allowed_read_pages or []
        allowed_write_pages = allowed_write_pages or []
        self._r_pages: set[int] = set(allowed_read_pages)
        self._w_pages: set[int] = set(allowed_write_pages)

        # sparse page map: page-number → bytearray(PAGE_SIZE)
        self._pages: Dict[int, bytearray] = {}
        if data:
            # bulk-load initial bytes
            for addr, val in data.items():
                if not (0 <= val <= 255):
                    raise ValueError(f"Memory: invalid value {val} @ {addr}")
                self._page_for(addr, create=True)[addr % PAGE_SIZE] = val

        self.heap_break: int = heap

    # --------------------------------------------------------------------- #
    # Core helpers
    # --------------------------------------------------------------------- #

    @staticmethod
    def _page_index(addr: int) -> int:
        return addr // PAGE_SIZE

    def _page_for(self, addr: int, *, create: bool = False) -> bytearray:
        """
        Get the underlying page buffer for an address.
        Creates a fresh zero-filled page if `create` is True.
        """
        pg = self._page_index(addr)
        try:
            return self._pages[pg]
        except KeyError:
            if not create:
                # return a read-only zero page (shared) to avoid dict hits
                return _ZERO_PAGE
            ba = bytearray(PAGE_SIZE)
            self._pages[pg] = ba
            return ba

    # fast, branch-free address checker
    def _assert_access(self, addr: int, *, write: bool = False) -> None:
        if addr < LOW_BOUND:
            raise Exception(f"Memory panic: address {addr} < {LOW_BOUND}")
        pg = self._page_index(addr)
        if write:
            if pg not in self._w_pages:
                logger.debug(f"Not allowed to write {addr}(Page={pg})")
                raise PvmError(PAGE_FAULT(addr))
        else:
            if pg not in self._r_pages and pg not in self._w_pages:
                logger.debug(f"Not allowed to read {addr}(Page={pg})")
                raise PvmError(PAGE_FAULT(addr))

    # --------------------------------------------------------------------- #
    # Public operations (interface unchanged)
    # --------------------------------------------------------------------- #

    def read(self, address: int, length: int) -> bytes:
        if length <= 0:
            return b""
        # Normalise once
        address = address % ADDR_MOD
        end = address + length

        out = bytearray(length)
        out_mv = memoryview(out)

        # iterate over pages spanned by the range
        cursor = 0
        while address < end:
            page_off = address % PAGE_SIZE
            chunk = min(PAGE_SIZE - page_off, end - address)

            # single access check per page instead of per-byte
            self._assert_access(address, write=False)
            src_page = self._page_for(address)  # ZERO_PAGE if never allocated
            out_mv[cursor : cursor + chunk] = src_page[page_off : page_off + chunk]

            address += chunk
            cursor += chunk
        return bytes(out)

    def write(self, address: int, data_bytes: bytes | Sequence[int]) -> None:
        if not data_bytes:
            return
        address = address % ADDR_MOD
        end = address + len(data_bytes)
        in_mv = memoryview(data_bytes)

        cursor = 0
        while address < end:
            page_off = address % PAGE_SIZE
            chunk = min(PAGE_SIZE - page_off, end - address)

            self._assert_access(address, write=True)
            dst_page = self._page_for(address, create=True)
            dst_page[page_off : page_off + chunk] = in_mv[cursor : cursor + chunk]

            address += chunk
            cursor += chunk

    def is_accessible(self, address: int, length: int, for_write: bool = False) -> bool:
        if length <= 0:
            return True
        pages = self.get_pages(address, length)
        if for_write:
            return all(pg in self._w_pages for pg in pages)
        return all(pg in self._r_pages or pg in self._w_pages for pg in pages)

    def dump_memory(self, start: int, end: int):  # debug helper
        return [
            (self._page_for(addr)[addr % PAGE_SIZE] if self._page_index(addr) in self._pages else 0)
            for addr in range(start, end)
        ]

    # repr / equality keep old behaviour for debugging or tests
    def __repr__(self):
        return f"Memory(pages={len(self._pages)}, read={sorted(self._r_pages)}, write={sorted(self._w_pages)})"

    def __eq__(self, other):
        if not isinstance(other, Memory):
            return NotImplemented
        if self._r_pages != other._r_pages or self._w_pages != other._w_pages:
            return False
        # compare only the cells both memories have explicitly written
        for pg, buf in self._pages.items():
            other_buf = other._pages.get(pg)
            if other_buf and buf != other_buf:
                return False
        for pg, buf in other._pages.items():
            self_buf = self._pages.get(pg)
            if self_buf and buf != self_buf:
                return False
        return True

    @classmethod
    def from_pc(cls, read: bytes, write: bytes, args: bytes, z: int, s: int) -> Self:
        memory = {}

        read_start = PVM_INIT_ZONE_SIZE
        read_pages = cls.get_pages(read_start, cls.total_page_size(len(read)))
        logger.debug(
            f"READ \t\t | Start: {int(read_start).to_bytes(4).hex()} \t | End {int(read_pages[-1] * PVM_MEMORY_PAGE_SIZE).to_bytes(4).hex()}"
        )
        for i, byt in enumerate(read):
            memory[read_start + i] = int(byt)

        write_start = 2 * PVM_INIT_ZONE_SIZE + cls.total_zone_size(len(read))
        write_pages = cls.get_pages(
            write_start,
            cls.total_page_size(len(write)) + (int(z) * PVM_MEMORY_PAGE_SIZE),
        )
        logger.debug(
            f"WRITE \t\t | Start: {int(write_start).to_bytes(4).hex()} \t | End {int((write_pages[-1] + 1) * PVM_MEMORY_PAGE_SIZE).to_bytes(4).hex()}"
        )
        for i, byt in enumerate(write):
            memory[write_start + i] = int(byt)

        heap = int((write_pages[-1] + 1) * PVM_MEMORY_PAGE_SIZE)

        write_pages.extend(
            cls.get_pages(
                2**32 - 2 * PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE - cls.total_page_size(s),
                cls.total_page_size(s),
            )
        )

        arg_start = 2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
        read_pages.extend(cls.get_pages(arg_start, cls.total_page_size(len(args))))
        logger.debug(f"ARG \t\t | START: {int(arg_start).to_bytes(4).hex()}")
        for i, byt in enumerate(args):
            memory[arg_start + i] = int(byt)

        return cls(memory, read_pages, write_pages, heap=heap)

    @staticmethod
    def total_page_size(blob_len: int) -> int:
        return PAGE_SIZE * ceil(blob_len / PAGE_SIZE)

    @staticmethod
    def total_zone_size(blob_len: int) -> int:
        return PVM_INIT_ZONE_SIZE * ceil(blob_len / PVM_INIT_ZONE_SIZE)

    @staticmethod
    def get_pages(start_index: int, length: int) -> List[int]:
        start = start_index // PAGE_SIZE
        end_index = start_index + max(length, 1) - 1
        end = end_index // PAGE_SIZE
        return list(range(start, end + 1))

    def zero_memory_range(self, start_address: int, offset: int):
        if offset <= 0:
            return
        end_address = start_address + offset
        while start_address < end_address:
            dst = self._page_for(start_address, create=True)
            pg_off = start_address % PAGE_SIZE
            chunk = min(PAGE_SIZE - pg_off, end_address - start_address)
            dst[pg_off : pg_off + chunk] = b"\x00" * chunk
            start_address += chunk

    def alter_accessibility(self, start_address: int, length: int, access_type: Accessibility):
        for pg in self.get_pages(start_address, length):
            if access_type == Accessibility.WRITE:
                self._w_pages.add(pg)
            else:
                self._r_pages.add(pg)


_ZERO_PAGE = bytes(PAGE_SIZE)
