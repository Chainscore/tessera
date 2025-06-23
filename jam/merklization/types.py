from tsrkit_types.choice import Choice
from tsrkit_types.integers import Uint
from tsrkit_types.sequences import Vector
from tsrkit_types.bytes import Bytes

class MerkleByte(Choice):
    byte: Bytes
    byte32: Bytes[32]