from tsrkit_types.sequences import TypedArray, TypedVector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, MAX_AUTH_QUEUE_ITEMS

AuthorizerHash = OpaqueHash

AuthorizationQueue = TypedArray[AuthorizerHash, MAX_AUTH_QUEUE_ITEMS]

Phi = TypedArray[AuthorizationQueue, CORE_COUNT]

AuthorizationVector = TypedVector[AuthorizerHash]

PhiVector = TypedVector[AuthorizationVector]
