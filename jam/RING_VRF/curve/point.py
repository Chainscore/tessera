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
        
        x, y = self.x, self.y
        y_bytes = bytearray(y.to_bytes(32, "little"))  # Convert y to byte array
        x_is_odd = x % 2  # Determine if x is odd (1) or even (0)

        # Set the MSB of the last byte to indicate parity of x
        y_bytes[-1] |= (x_is_odd << 7)

        return bytes(y_bytes)


    @staticmethod
    def _get_bit(h, i):
        """Return the specified bit from a byte sequence."""
        h1 = int.from_bytes(h, 'little')
        return (h1 >> i) & 0x01
