
from typing import List
from jam.types.base.integers.fixed import U8
from jam.types.base.sequences.vector import Vector, decodable_vector

@decodable_vector(U8)
class Zeta(Vector):
    """
    Zeta is a vector of instructutions, padding with an indefinite number of 0s to ensure out of bounds errors are not encountered
    TODO: Implement indefinite padding
    """
    def __init__(self, instructions: List[U8]):
        super().__init__(instructions + [U8(0)] * 1000)