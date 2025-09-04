from tsrkit_types.bytes import Bytes


def decode_code_hash(service_data: bytes | Bytes) -> (bytes, bytes):
    if not service_data:
        raise ValueError("Service code not found")
    pm, offset = Bytes.decode_from(bytes(service_data))
    pc = service_data[offset:]
    return pm, pc
