
from typing import Any, List, Sequence
from jam.types.base.integers.fixed import U8
from jam.types.base.sequences.vector import Vector, decodable_vector

@decodable_vector(U8)
class Zeta(Vector):
    """
    Zeta is a vector of instructutions, padding with an indefinite number of 0s to ensure out of bounds errors are not encountered
    TODO: Test indefinite padding
    """
    def __init__(self, instructions: List[U8]):
        super().__init__(instructions + [U8(0)] * 1000)

    # def __getitem__(self, index: int | slice | U8) -> Any | Sequence:
    #     if isinstance(index, int):
    #         if index >= len(self):
    #             return U8(0)
    #         else:
    #             return super().__getitem__(index)
    #     elif isinstance(index, slice):
    #         return [self[i] if i < len(self) else U8(0) for i in range(index.start, index.stop, index.step)]