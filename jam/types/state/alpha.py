from tsrkit_types import TypedBoundedVector
from tsrkit_types.sequences import TypedArray, TypedVector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, O

AuthorizerHash = OpaqueHash

AuthorizationPool = TypedBoundedVector[AuthorizerHash, 0, O]

class Alpha(TypedArray[AuthorizationPool, CORE_COUNT]):
    """
    Component: α
    Key: 1

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/103a00104600?v=0.7.0
    """

    ...
