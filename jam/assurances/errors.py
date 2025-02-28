from jam.error import JamError
from jam.types.base.enum import Enum, decodable_enum


class AssurancesError(JamError):
    ...


@decodable_enum
class AssurancesErrorCode(Enum):
    """Error codes for the Assurances part of the Extrinsics."""

    BAD_ATTESTATION_PARENT = "bad-attestation-parent"  # Parent block hash does not match attestation
    BAD_VALIDATOR_INDEX = "bad-validator-index"  # Invalid validator index
    CORE_NOT_ENGAGED = "core-not-engaged"  # Core is not engaged for work
    BAD_SIGNATURE = "bad-signature"  # Invalid signature
    NOT_SORTED_OR_UNIQUE_ASSURERS = "not-sorted-or-unique-assurers"  # Assurers not sorted or contain duplicates
