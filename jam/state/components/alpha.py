from jam.types import Vector, Array
from jam.types.base.sequences.array import decodable_array
from jam.types.base.sequences.vector import decodable_vector
from jam.types.protocol.crypto import OpaqueHash
from jam.utils.constants import MAX_AUTH_POOL_ITEMS

AuthorizerHash = OpaqueHash

@decodable_array(length=MAX_AUTH_POOL_ITEMS, element_type=AuthorizerHash)
class AuthorizationPool(Vector[AuthorizerHash]): 
    """Authorization pool to have upto MAX_AUTH_POOL_ITEMS auth hashes"""
    ...

@decodable_vector(element_type=AuthorizationPool)
class Alpha(Array[AuthorizationPool]): 
    """α Alpha is an array of authorization pools for all cores"""
    ...