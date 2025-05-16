from jam.utils.codec.primitives.bytes import BytesCodec


def decode_code_hash(service_data: bytes) -> (bytes, bytes):
    pm, offset = BytesCodec.decode_from(bytes(service_data))
    pc = service_data[offset:]
    return pm, pc
