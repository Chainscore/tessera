from tsrkit_types.enum import Enum
from jam.error import JamError


class PreimageError(JamError):
    pass


class PreimageErrorEnum(Enum):
    PREIMAGE_UNNEEDED = "preimage_unneeded"
    PREIMAGE_NOT_SORTED_UNIQUE = "preimages_not_sorted_unique"
