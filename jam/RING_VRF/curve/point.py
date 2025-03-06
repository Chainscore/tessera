class Point:
    x: int
    y: int

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def point_to_string(self):
        """
        Convert elliptic curve point (x, y) to compressed octet string.
        - The x-coordinate is encoded as 32 bytes.
        - The most significant bit of the last byte indicates the parity of y.
        """
        
        p = self.curve.PRIME_FIELD
        p_half = (p - 1) // 2
        x, y = self.x, self.y
        y_bytes = bytearray(y.to_bytes(32, "little"))  # Encode y in little-endian
        x_sign_bit = 1 if x >= p_half else 0  # Sign is set if x >= p/2
        y_bytes[-1] |= (x_sign_bit << 7)
        return bytes(y_bytes)

    @staticmethod
    def _get_bit(h, i):
        """Return the specified bit from a byte sequence."""
        h1 = int.from_bytes(h, 'little')
        return (h1 >> i) & 0x01
