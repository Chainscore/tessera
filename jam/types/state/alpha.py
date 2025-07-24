from tsrkit_types.sequences import TypedArray, TypedVector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT

AuthorizerHash = OpaqueHash

AuthorizationPool = TypedVector[AuthorizerHash]


# State key: 1
class Alpha(TypedArray[AuthorizationPool, CORE_COUNT]):
    ...
