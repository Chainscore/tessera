import os

def test_read_srs_file():
    filename = "tests/unit/vrf/data/srs/bls12-381-srs-2-11-uncompressed-zcash.bin"
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")

    with open(filename, "rb") as f:
        data = f.read()

    # The first 8 bytes form a little-endian uint64 that gives the number of G1 elements.
    if len(data) < 8:
        raise ValueError("File too short to contain header.")
    header = data[:8]
    g1_count = int.from_bytes(header, byteorder="little")
    print(f"Number of G1 elements: {g1_count}")

    offset = 8
    G1_POINT_SIZE = 96  # 2 * 48-byte field elements.
    G1_points = []
    for i in range(g1_count):
        point_bytes = data[offset:offset + G1_POINT_SIZE]
        if len(point_bytes) != G1_POINT_SIZE:
            raise ValueError(f"Unexpected end-of-file when reading G1 point {i}.")
        x_bytes = point_bytes[:48]
        y_bytes = point_bytes[48:]
        x = int.from_bytes(x_bytes, byteorder="little")
        y = int.from_bytes(y_bytes, byteorder="little")
        G1_points.append((x, y))
        offset += G1_POINT_SIZE

    G2_POINT_SIZE = 192  # 2 coordinates, each with 2*48 bytes.
    G2_points = []
    # There are exactly 2 G2 points at the end of the file.
    for i in range(2):
        point_bytes = data[offset:offset + G2_POINT_SIZE]
        if len(point_bytes) != G2_POINT_SIZE:
            raise ValueError(f"Unexpected end-of-file when reading G2 point {i}.")
        x0 = int.from_bytes(point_bytes[0:48], byteorder="little")
        x1 = int.from_bytes(point_bytes[48:96], byteorder="little")
        y0 = int.from_bytes(point_bytes[96:144], byteorder="little")
        y1 = int.from_bytes(point_bytes[144:192], byteorder="little")
        G2_points.append(((x0, x1), (y0, y1)))
        offset += G2_POINT_SIZE

    g1_points, g2_points = G1_points, G2_points

    print(f"Found total of {len(g1_points)} G1 points")
    print(f"Found total of {len(g2_points)} G2 points")
    print("First G1 point:", g1_points[0])
    print("First G2 point:", g2_points[0])
