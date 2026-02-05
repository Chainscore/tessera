from tsrkit_types.sequences import TypedArray, TypedVector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, MAX_AUTH_QUEUE_ITEMS

AuthorizerHash = OpaqueHash


class AuthorizationQueue(TypedArray[AuthorizerHash, MAX_AUTH_QUEUE_ITEMS]):
    ...


class Phi(TypedArray[AuthorizationQueue, CORE_COUNT]):
    """
    Component: ϕ
    Key: 2

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/103a00104f00?v=0.7.0
    """

    ...