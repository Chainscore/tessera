from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum

class AuditingError(JamError):
    ...

@decodable_enum
class AuditingErrorCode(Enum):
    """Error codes for the Reporting"""


