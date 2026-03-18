from jam.error import JamError
from tsrkit_types.enum import Enum


class NetworkingError(JamError):
    """error type for networking module"""

    ...


class NetworkingErrorCode(Enum):
    SYNC_ERROR = "Node not synchronized."
    NO_PEER = "Peer information not available."
    INVALID_QUERY = "Invalid Query."
    DATA_UNAVAILABLE = "Requested data not available."
    INVALID_DATA = "Buffer length & Message length mismatch."
    BAD_RESPONSE = "Error parsing response."
    NO_PEER_CONN = "Peer not connected."
