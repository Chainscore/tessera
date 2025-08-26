from typing import Self
from jam.utils.constants import PVM_INIT_DATA_SIZE, PVM_INIT_ZONE_SIZE


def from_pc(args) -> Self:
    result = [0] * 13
    result[0] = 2**32 - 2**16
    result[1] = 2**32 - 2 * PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
    result[7] = 2**32 - PVM_INIT_ZONE_SIZE - PVM_INIT_DATA_SIZE
    result[8] = len(args)
    return result
