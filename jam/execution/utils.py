from typing import Tuple
from tsrkit_types.bytes import Bytes


def decode_code_hash(service_data: bytes | Bytes) -> Tuple[bytes|None, bytes|None]:
    if not service_data:
        return None, None 
    pm, offset = Bytes.decode_from(bytes(service_data))
    pc = service_data[offset:]
    return bytes(pm), bytes(pc)
