import hashlib


def fiat_shamir_hash(*inputs):
    hasher = hashlib.sha256()
    for item in inputs:
        # Ensure each input is converted to bytes
        if isinstance(item, int):
            hasher.update(item.to_bytes((item.bit_length() + 7) // 8, byteorder="big"))
        elif isinstance(item, str):
            hasher.update(item.encode("utf-8"))
        elif isinstance(item, bytes):
            hasher.update(item)
        else:
            # Given large number (convert to string)
            large_number_str = str(item)

            # Convert to bytes
            large_number_bytes = large_number_str.encode("utf-8")

            # Compute SHA-256 hash
            hash_object = hashlib.sha256(large_number_bytes)
            hash_hex = hash_object.hexdigest()
            return hash_hex

    # Return the hash as a hexadecimal string
    return hasher.hexdigest()


def split_hash_into_chunks(commitment, num_chunks=7):
    hash_hex = hashlib.sha256(str(commitment).encode("utf-8")).hexdigest()
    # Split hash into equal chunks
    chunk_size = len(hash_hex) // num_chunks
    chunks = [hash_hex[i : i + chunk_size] for i in range(0, len(hash_hex), chunk_size)]

    # Convert hexadecimal string chunks to integers
    return [int(chunk, 16) for chunk in chunks]


def construct_the_aggregated_polynomial(chunks, c1x, c2x, c3x, c4x, c5x, c6x, c7x):
    # hash_hex = fiat_shamir_hash(commitment)
    cx = (
        c1x * chunks[0]
        + c2x * chunks[1]
        + c3x * chunks[2]
        + c4x * chunks[3]
        + c5x * chunks[4]
        + c6x * chunks[5]
        + c7x * chunks[6]
    )
    return cx


def construct_the_agg_x(chunks, px, py, sx, bx, accipx, accxx, accyx, qx):
    agg_x = (
        px * chunks[0]
        + py * chunks[1]
        + sx * chunks[2]
        + bx * chunks[3]
        + accipx * chunks[4]
        + accxx * chunks[5]
        + accyx * chunks[6]
        + qx * chunks[7]
    )
    return agg_x
