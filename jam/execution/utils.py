from tsrkit_types.bytes import Bytes


def decode_code_hash(service_data: bytes|Bytes) -> (bytes, bytes):
    print("service data", service_data)
    pm, offset = Bytes.decode_from(bytes(service_data))
    pc = service_data[offset:]
    return pm, pc
