from tsrkit_types.sequences import TypedArray, TypedVector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, MAX_AUTH_QUEUE_ITEMS

AuthorizerHash = OpaqueHash


class AuthorizationQueue(TypedArray[AuthorizerHash, MAX_AUTH_QUEUE_ITEMS]):
    ...


# State key: 2
class Phi(TypedArray[AuthorizationQueue, CORE_COUNT]):
    ...


class AuthorizationVector(TypedVector[AuthorizerHash]):
    ...


class PhiVector(TypedVector[AuthorizationVector]):
    ...
