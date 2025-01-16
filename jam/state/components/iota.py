from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import VALIDATOR_COUNT

@decodable_array(VALIDATOR_COUNT, ValidatorData)
class Iota(Array[ValidatorData]): 
    """Staging set of validators"""
    ...
