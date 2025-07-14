from enum import Enum
from jam.error import JamError


class BlockErrorCode(Enum):
    INCORRECT_EXTRINSIC_HASH = 0
    INVALID_SEAL = 1
    INVALID_ENTROPY = 2
    SIGNER_MISMATCH = 3
    INVALID_PARENT = 4
    INVALID_TIMESLOT = 5
    INVALID_AUTHOR = 6
    EPOCH_MARKER_NOT_EMPTY = 7
    EPOCH_MARKER_EMPTY = 8
    TICKETS_MARK_NOT_EMPTY = 9
    TICKETS_MARK_EMPTY = 10
    INCORRECT_STATE_ROOT = 11


class BlockError(JamError):
    ...
