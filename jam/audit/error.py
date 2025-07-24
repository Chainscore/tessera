from tsrkit_types import Enum
from jam.error import JamError


class AuditingError(JamError):
    ...


class AuditingErrorCode(Enum):
    """Error codes for the Reporting"""
