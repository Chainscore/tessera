from typing import Tuple, Union
from jam.types.base import Byte
from jam.types.base.integers.fixed import U8, U32
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.protocol.core import ServiceId


def construct_state_key(
    input: Union[U8, int, Tuple[U32, ServiceId], Tuple[ServiceId, ByteArray32]]
) -> ByteArray32:
    """
    State key constructor function C as defined in Appendix D.
    Maps inputs to a 32-byte hash according to three cases:
    1. Single U8 index i -> [i, 0, 0, ...]
    2. (i, s) where i is U32 and s is ServiceId -> [i, n₀, 0, n₁, 0, n₂, 0, n₃, 0, 0, ...] where n = E₄(s)
    3. (s, h) where s is ServiceId and h is 32-byte array -> [n₀, h₀, n₁, h₁, n₂, h₂, n₃, h₃, h₄, h₅, ..., h₂₇] where n = E₄(s)
    """
    sequence = ByteArray32([0] * 32)

    if isinstance(input, U8) or isinstance(input, int):
        # Case 1: Single U8 index
        sequence[0] = Byte(U8(input).value)

    elif isinstance(input, tuple) and len(input) == 2:
        if isinstance(input[0], U8) and isinstance(input[1], ServiceId):
            # Case 2: (U8, ServiceId - U32)
            index, service_id = input
            service_id_encoded = service_id.encode()
            sequence[0] = Byte(index.value)
            for i, s_byte in enumerate(service_id_encoded):
                sequence[i + 1] = Byte(s_byte)
                i += 2

        elif isinstance(input[0], ServiceId) and isinstance(input[1], ByteArray32):
            # Case 3: (ServiceId, ByteArray32[0:28])
            service_id, hash_bytes = input
            service_id_encoded = service_id.encode()
            seq_pointer = 0
            h_pointer = 0
            while seq_pointer < 32:
                if len(service_id_encoded) > h_pointer:
                    sequence[seq_pointer] = Byte(service_id_encoded[h_pointer])
                    sequence[seq_pointer + 1] = hash_bytes[h_pointer]
                    h_pointer += 1
                    seq_pointer += 2
                else:
                    sequence[seq_pointer:32] = hash_bytes[h_pointer:28]
                    break

        else:
            raise ValueError("Invalid tuple input types")
    else:
        raise ValueError("Invalid input type")

    return sequence
