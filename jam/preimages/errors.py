from jam.types.base.enum import Enum

class PreimageError(Exception):
    pass

class PreimageErrorEnum(Enum):
    PREIMAGE_UNNEEDED = "preimage_unneeded"
    PREIMAGE_NOT_SORTED_UNIQUE = "preimages_not_sorted_unique"
