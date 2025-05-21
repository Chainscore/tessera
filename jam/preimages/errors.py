from jam.types.base.enum import Enum, decodable_enum
from jam.error import JamError

class PreimageError(JamError):
    pass

@decodable_enum
class PreimageErrorEnum(Enum):

    PREIMAGE_UNNEEDED = "preimage_unneeded"
    PREIMAGE_NOT_SORTED_UNIQUE = "preimages_not_sorted_unique"
