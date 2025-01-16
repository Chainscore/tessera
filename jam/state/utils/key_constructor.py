from typing import Tuple, Union
from jam.types.base.integers.fixed import U8, U32
from jam.types.base.sequences.byte_array import ByteArray32
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
        sequence[0] = input
        
    elif isinstance(input, tuple) and len(input) == 2:
        if isinstance(input[0], U8) and isinstance(input[1], ServiceId):
            # Case 2: (U8, ServiceId - U32)
            index, service_id = input
            service_id_encoded = service_id.encode()
            sequence[0] = index.encode()
            for i, s_byte in enumerate(service_id_encoded):
                sequence[i+1] = s_byte
                i += 2
            
        elif isinstance(input[0], ServiceId) and isinstance(input[1], ByteArray32):
            # Case 3: (ServiceId, ByteArray32[0:28])
            service_id, hash_bytes = input
            service_id_encoded = service_id.encode()
            seq_pointer = 0         
            h_pointer = 0  
            while seq_pointer < 32:
                if len(service_id_encoded) > h_pointer:
                    print("Adding sid [", h_pointer, "] + hex [", h_pointer + 1, "]:", service_id_encoded[h_pointer], hash_bytes[h_pointer])
                    sequence[seq_pointer] = service_id_encoded[h_pointer]
                    sequence[seq_pointer + 1] = hash_bytes[h_pointer]
                    h_pointer += 1
                    seq_pointer += 2
                else:
                    print("Adding hash [", h_pointer, "] + hex [", 32, "]:", hash_bytes[h_pointer:32])
                    sequence[seq_pointer:32] = hash_bytes[h_pointer:32]
                    break

        else:
            raise ValueError("Invalid tuple input types")
    else:
        raise ValueError("Invalid input type")
    
    return sequence

# [Byte(0x03), Byte(0x04), Byte(0x05), Byte(0x06), Byte(0x07), Byte(0x08), Byte(0x09), Byte(0x0a), Byte(0x0b), Byte(0x0c), Byte(0x0d), Byte(0x0e), Byte(0x0f), Byte(0x10), Byte(0x11), Byte(0x12), Byte(0x13), Byte(0x14), Byte(0x15), Byte(0x16), Byte(0x17), Byte(0x18), Byte(0x19), Byte(0x1a)]
# [            Byte(0x04), Byte(0x05), Byte(0x06), Byte(0x07), Byte(0x08), Byte(0x09), Byte(0x0a), Byte(0x0b), Byte(0x0c), Byte(0x0d), Byte(0x0e), Byte(0x0f), Byte(0x10), Byte(0x11), Byte(0x12), Byte(0x13), Byte(0x14), Byte(0x15), Byte(0x16), Byte(0x17), Byte(0x18), Byte(0x19), Byte(0x1a), Byte(0x1b), Byte(0x1c), Byte(0x1d), Byte(0x1e), Byte(0x1f)]