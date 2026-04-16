from typing import Tuple, Union
from jam.models import Hash
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U8, U32, Uint


def construct_state_key(input: Union[U8, Tuple[U32, Bytes], Tuple[U8, U32]]) -> Bytes:
    """
    State key constructor function C as defined in Appendix D.
    Maps inputs to a 31-byte hash according to three cases:
    1. Single U8 index i -> [i, 0, 0, ...]
    2. (i, s) where i is U32 and s is ServiceId -> [i, n₀, 0, n₁, 0, n₂, 0, n₃, 0, 0, ...] where n = E₄(s)
    3. (s, h) -> [n₀, a₀, n₁, a₁, n₂, a₂, n₃, a₃, a₄, a₅, ..., a₂₆] where n = E₄(s) and a = H(h)
    """
    sequence = [0] * 31

    if isinstance(input, (U8, int)):
        # Case 1: Single U8 index
        sequence[0] = int(input)

    elif isinstance(input, tuple) and len(input) == 2:
        if isinstance(input[0], (U8, int)) and isinstance(input[1], (U32, int)):
            # Case 2: (U8, ServiceId - U32)
            index, service_id = input
            service_id_encoded = Uint[32](service_id).encode()
            sequence[0] = index
            start = 1
            for i, s_byte in enumerate(service_id_encoded):
                sequence[start] = s_byte
                start += 2

        elif isinstance(input[0], (U32, int)) and isinstance(input[1], (Bytes, bytes)):
            # Case 3: (ServiceId, Bytes)
            service_id, key = input
            hash_bytes = Hash.blake2b(key)
            service_id_encoded = Uint[32](service_id).encode()
            seq_pointer = 0
            a_pointer = 0
            while seq_pointer < 31:
                if len(service_id_encoded) > a_pointer:
                    sequence[seq_pointer] = service_id_encoded[a_pointer]
                    sequence[seq_pointer + 1] = hash_bytes[a_pointer]
                    a_pointer += 1
                    seq_pointer += 2
                else:
                    sequence[seq_pointer:31] = hash_bytes[a_pointer:27]
                    break

        else:
            raise ValueError(f"Invalid input type - {input} of type {type(input)}")
    else:
        raise ValueError(f"Invalid input type - {input} of type {type(input)}")

    return Bytes(sequence)