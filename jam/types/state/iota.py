from tsrkit_types.sequences import TypedArray
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import VALIDATOR_COUNT


# State key: 7
class Iota(TypedArray[ValidatorData, VALIDATOR_COUNT]):
    ...
