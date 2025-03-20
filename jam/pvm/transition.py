from jam.utils.codec.decorators.dataclasses import decodable_dataclass, Codable
from dataclasses import dataclass
from jam.pvm.memory import MemoryChunk
from jam.pvm.page_map import PageMap
from jam.pvm.pvm_memory import PageMemory, Memory, Access, Pages
from jam.types.base.sequences.bytes.bytes import Bytes, Byte
from jam.types.base.integers.fixed import U32
from jam.types.base.boolean import Boolean


@decodable_dataclass
@dataclass
class PvmTransition(Codable):

    memory: PageMemory

    def __init__(self, memory: PageMemory):
        self.memory = memory

    @staticmethod
    def transit(json_memory: MemoryChunk, page: PageMap, isPage: bool = True):
        page_structure = Pages()

        # Convert PageMap into a lookup dictionary for fast access
        page_lookup = {p.address: p for p in page}

        if not isPage:
            # Process memory data as usual
            for mem in json_memory:
                page_key = U32(mem.address // 4096)  # Page index calculation
                offset = mem.address % 4096  # Calculate offset within the page

                if page_key not in page_structure:
                    page_structure[page_key] = Memory(
                        value=Bytes([Byte(0)] * 4096),  # Initialize with 4096 Byte(0)
                        access=Access(inaccessible=Boolean(True), writable=Boolean(False), readable=Boolean(False))
                    )

                # Store memory data starting from offset
                for i, byte in enumerate(mem.contents):
                    if offset + i < 4096:  # Ensure within bounds
                        page_structure[page_key].value[offset + i] = byte

                # Determine access permissions
                page_info = page_lookup.get(mem.address, None)
                page_structure[page_key].access = Access(
                    inaccessible=Boolean(False),
                    writable=page_info.is_writable if page_info else Boolean(False),
                    readable=Boolean(True) if page_info and page_info.is_writable else Boolean(False),
                )
        else:
            # Process based on pageMap instead
            for p in page:
                page_key = U32(p.address // 4096)
                offset = p.address % 4096  # Calculate offset within the page

                if page_key not in page_structure:
                    page_structure[page_key] = Memory(
                        value=Bytes([Byte(0)] * 4096),
                        access=Access(inaccessible=Boolean(True), writable=Boolean(False), readable=Boolean(False))
                    )

                # Assign access permissions
                page_structure[page_key].access = Access(
                    inaccessible=Boolean(False),
                    writable=p.is_writable,
                    readable=Boolean(True)
                ) if p.is_writable else Access(
                    inaccessible=Boolean(False),
                    writable=Boolean(False),
                    readable=Boolean(True)
                )

            # Fix: Iterate over json_memory to accumulate memory values properly
            for mem in json_memory:
                page_key = U32(mem.address // 4096)  # Calculate page index
                offset = mem.address % 4096  # Offset within the page

                if page_key in page_structure:
                    for i, byte in enumerate(mem.contents):
                        if offset + i < 4096:  # Ensure within bounds
                            page_structure[page_key].value[offset + i] = byte

        memory_structure = PageMemory(page_structure)
        return memory_structure




