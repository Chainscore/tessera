from jam.types import ByteArray32


class MountainMerkle:
    """General Merklization implementation for Merkle Mountain Ranges as defined in Section E.2"""

    def __init__(self):
        self._ZERO_HASH = ByteArray32([0] * 32)