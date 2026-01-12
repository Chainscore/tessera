from enum import Enum
from jam.error import JamError


class BlockErrorCode(Enum):
    INCORRECT_EXTRINSIC_HASH = "Incorrect extrinsic hash"
    INVALID_SEAL = "Invalid header seal"
    INVALID_ENTROPY = "Invalid entropy signature"
    SIGNER_MISMATCH = "Unexpected signer"
    INVALID_PARENT = "Incorrect parent header"
    INVALID_TIMESLOT = "Invalid timeslot"
    INVALID_AUTHOR = "Author is invalid"
    EPOCH_MARKER_NOT_EMPTY = "Epoch marker is supposed to be empty"
    INVALID_EPOCH_MARK = "Epoch marker is invalid"
    EPOCH_MARKER_EMPTY = "Got empty epoch marker on new epoch"
    TICKETS_MARK_NOT_EMPTY = "Tickets mark is supposed to be empty"
    INVALID_TICKET_MARK = "Ticket marker is invalid"
    TICKETS_MARK_EMPTY = "Got empty ticket mark when we have accumulated tickets + new epoch"
    INCORRECT_STATE_ROOT = "Incorrect state root"


class BlockError(JamError):
    ...
