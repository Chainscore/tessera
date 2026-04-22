from tsrkit_types import structure, TypedVector

from jam.models.protocol.core import ServiceId
from jam.models.protocol.crypto import OpaqueHash

@structure
class Commitment:
    service_id: ServiceId
    output: OpaqueHash

class Theta(TypedVector[Commitment]):
    """
    Component: θ
    Key: 16

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/0f6b020f7702?v=0.7.0
    """

    ...