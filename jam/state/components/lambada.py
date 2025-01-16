from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import VALIDATOR_COUNT

@decodable_array(VALIDATOR_COUNT, ValidatorData)
class Lambada(Array[ValidatorData]): 
    """Previous epoch's validator keys and metadata."""
    ...
