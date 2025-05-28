from typing import Any, List, Union


class Zeta(list):
    """
    Zeta is a vector of instructutions, padding with an indefinite number of 0s to ensure out of bounds errors are not encountered
    TODO: Test
    """
    def __getitem__(self, index):
        if isinstance(index, int):
            if -len(self) <= index < len(self):
                return super().__getitem__(index)
            else:
                return 0
        elif isinstance(index, slice):
            # Figure out the actual indices that the slice would return
            start, stop, step = index.indices(len(self))
            result = [self[i] if 0 <= i < len(self) else 0 for i in range(start, stop, step)]
            return result
        else:
            raise TypeError("Invalid argument type.")