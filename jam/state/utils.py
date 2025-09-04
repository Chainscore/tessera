from typing import Tuple, Type, Union

from tsrkit_types import Codable

from jam.types import Hash
from jam.types.protocol.core import ServiceId
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U8, U32, Uint


def construct_state_key(input: Union[U8, Tuple[U32, Bytes], Tuple[U8, U32]]) -> Bytes:
    """
    State key constructor function C as defined in Appendix D.
    Maps inputs to a 31-byte hash according to three cases:
    1. Single U8 index i -> [i, 0, 0, ...]
    2. (i, s) where i is U32 and s is ServiceId -> [i, n₀, 0, n₁, 0, n₂, 0, n₃, 0, 0, ...] where n = E₄(s)
    3. (s, h) where s is ServiceId and h is 27-byte array -> [n₀, h₀, n₁, h₁, n₂, h₂, n₃, h₃, h₄, h₅, ..., h₂₇] where n = E₄(s)
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
            # Case 3: (ServiceId, Bytes[0:27])
            service_id, key = input
            hash_bytes = Hash.blake2b(key)
            service_id_encoded = Uint[32](service_id).encode()
            seq_pointer = 0
            h_pointer = 0
            while seq_pointer < 31:
                if len(service_id_encoded) > h_pointer:
                    sequence[seq_pointer] = service_id_encoded[h_pointer]
                    sequence[seq_pointer + 1] = hash_bytes[h_pointer]
                    h_pointer += 1
                    seq_pointer += 2
                else:
                    sequence[seq_pointer:31] = hash_bytes[h_pointer:27]
                    break

        else:
            raise ValueError(f"Invalid input type - {input} of type {type(input)}")
    else:
        raise ValueError(f"Invalid input type - {input} of type {type(input)}")

    return Bytes(sequence)


def make_state_prop(state_key: int, cl: Type[Codable]):
    def fget(self):
        raw = self.store.get(construct_state_key(state_key))
        if raw is None:
            raise ValueError(f"State component missing from DB: {cl.__name__}")
        return cl.decode_from(raw)[0]

    def fset(self, value):
        k, v = construct_state_key(state_key), value.encode()
        self.store.put(bytes(k), v)

    return property(fget, fset)