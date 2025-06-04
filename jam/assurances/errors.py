from tsrkit_types.enum import Enum

class AssuranceError(Enum):
    INVALID_ASSURANCE = "Invalid assurance format"
    VERIFICATION_FAILED = "Assurance verification failed"
    EXPIRED_ASSURANCE = "Assurance has expired"
