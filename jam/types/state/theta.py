from tsrkit_types import structure, TypedVector

from jam.types.protocol.core import ServiceId
from jam.types.protocol.crypto import OpaqueHash

@structure
class Commitment:
    service_id: ServiceId
    output: OpaqueHash

# State Key: 16
# Stores Most Recent Accumulated Outputs / Commitments
class Theta(TypedVector[Commitment]):
    ...