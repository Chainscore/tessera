from tsrkit_types import Enum
from jam.error import JamError


class AuditingError(JamError):
    ...


class AuditingErrorCode(Enum):
    """Error codes for the Reporting"""

class AssemblerError(JamError):
    ...


class AssemblerErrorCode(Enum):
    INVALID_RESPONSE = "No shard received"
    INCORRECT_SHARD = "Invalid Shard Received"
    SHARDS_UNAVAILABLE = "Not enough shards available"
    FAULTY_BUNDLE = "Bundle is invalid"