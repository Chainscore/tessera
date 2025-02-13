from typing import Optional

from jam.types import Vector
from jam.types.base.sequences.bytes import ByteArray32
from jam.types.protocol.crypto import Hash
# import math

HashType = ByteArray32

def _preprocessor_fn(values: Vector[ByteArray32], hash_fn: Optional[Hash] = Hash.sha256) -> Vector[HashType]:
    """Constancy Preprocessor Function Implementation as defined in Equation E.7 in Section E.1.2"""
    new_values: Vector[HashType] = Vector()

    for val in values:
        new_val = hash_fn('leaf' + val)
        new_values.append(new_val)

    return new_values

class BinaryMerkle:
    """General Merklization implementation for Binary Trees as defined in Section E.1"""

    def __init__(self):
        self._ZERO_HASH = ByteArray32([0] * 32)

    def _node_fn(self, values: Vector[ByteArray32], hash_fn: Optional[Hash] = Hash.sha256) -> HashType:
        """Node Function Implementation as defined in Equation E.1"""

        if len(values) == 0:
            return self._ZERO_HASH
        elif len(values) == 1:
            return values[0]
        else:
            left = values[:len(values) // 2]
            right = values[len(values) // 2:]
            return hash_fn('node' + self._node_fn(left, hash_fn) + self._node_fn(right, hash_fn))

    def wb_merkle_fn(self, values: Vector[ByteArray32], hash_fn: Optional[Hash] = Hash.sha256) -> HashType:
        """Well Balanced Binary Merkle Function Implementation as defined in Equation E.3 in Section E.1.1"""

        if len(values) == 1:
            return hash_fn(values[0])
        else:
            return self._node_fn(values, hash_fn)

    def cd_merkle_fn(self, values: Vector[ByteArray32], hash_fn: Optional[Hash] = Hash.sha256) -> HashType:
        """Constant Depth Binary Merkle Function Implementation as defined in Equation E.4 in Section E.1.2"""

        return self._node_fn(_preprocessor_fn(values, hash_fn), hash_fn)