from jam.pvm.memory import Memory, MemoryChunk
from jam.pvm.pvm_memory import PageMemory
from jam.pvm.register import Registers
from jam.types.base.integers.fixed import U16, U24
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.utils.constants import REGISTER_COUNT


def derive_p(program: bytes) -> (Bytes, Registers, PageMemory):
    try:
        (c, o, w, _, _) = decode_program(program)
        return c, o, w
    except Exception:
        return None


def decode_program(program: bytes) -> (Bytes, Registers, PageMemory, U16, U24):
    offset = 0
    o_len = U24.decode_from(program, offset)
    if o_len[0] != REGISTER_COUNT:
        raise Exception("Invalid register count")
    offset += 3
    w_len = U24.decode_from(program, offset)
    offset += 3
    z = U16.decode_from(program, offset)
    offset += 2
    s = U24.decode_from(program, offset)
    offset += 3
    # Decoding registers
    o, decoded = Registers.decode_from(program, offset)
    offset += decoded

    # Decoding memory
    @decodable_array(length=w_len[0], item=Memory)
    class MemoryArray(Array):
        ...

    w, decoded = MemoryArray.decode_from(program, offset)
    offset += decoded
    # Decoding code
    c, decoded = Bytes.decode_from(program, offset)
    return c, o, PageMemory(w), z, s
