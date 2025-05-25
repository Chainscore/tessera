from typing import Any, List, Union


class Zeta(list):
    """
    Zeta is a vector of instructutions, padding with an indefinite number of 0s to ensure out of bounds errors are not encountered
    TODO: Test
    """
    def __init__(self, instructions: List):
        super().__init__(instructions + [0] * 1000)
