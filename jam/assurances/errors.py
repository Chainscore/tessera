from tsrkit_types import Enum
from jam.error import JamError


class AssurancesError(JamError):
    ...

class AssurancesErrorCode(Enum):
    """Error codes for the Assurances part of the Extrinsics."""

    BAD_ATTESTATION_PARENT = "bad_attestation_parent"  # Parent block hash does not match attestation
    BAD_VALIDATOR_INDEX = "bad_validator_index"  # Invalid validator index
    CORE_NOT_ENGAGED = "core_not_engaged"  # Core is not engaged for work
    BAD_SIGNATURE = "bad_signature"  # Invalid signature
    NOT_SORTED_OR_UNIQUE_ASSURERS = "not_sorted_or_unique_assurers"  # Assurers not sorted or contain duplicates