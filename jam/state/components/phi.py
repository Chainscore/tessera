from jam.types import Array
from jam.types.base.sequences.array import decodable_array

# from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, MAX_AUTH_QUEUE_ITEMS

AuthorizerHash = OpaqueHash


@decodable_array(length=MAX_AUTH_QUEUE_ITEMS, element_type=AuthorizerHash)
class AuthorizationQueue(Array[AuthorizerHash]):
    """Authorization queue to have upto MAX_AUTH_QUEUE_ITEMS auth hashes"""

    ...


@decodable_array(length=CORE_COUNT, element_type=AuthorizationQueue)
class Phi(Array[AuthorizationQueue]):
    """φ Phi is an array of authorization queues for all cores"""

    ...
