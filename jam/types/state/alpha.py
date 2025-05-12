from jam.types import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import CORE_COUNT, MAX_AUTH_POOL_ITEMS

AuthorizerHash = OpaqueHash


@decodable_vector(element_type=AuthorizerHash)
class AuthorizationPool(Vector[AuthorizerHash]):
    """Authorization pool to have upto MAX_AUTH_POOL_ITEMS auth hashes"""

    ...


@decodable_array(length=CORE_COUNT, element_type=AuthorizationPool)
class Alpha(Array[AuthorizationPool]):
    """α Alpha is an array of authorization pools for all cores"""

    ...
