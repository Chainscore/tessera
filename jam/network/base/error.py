from jam.error import JamError
from tsrkit_types.enum import Enum

class NetworkingError(JamError):
    ...

class NetworkingErrorCode(Enum):
    NO_PEER = "Peer information not available."
    INVALID_DATA = "Buffer length & Message length mismatch."
    BAD_RESPONSE = "Error parsing response."
