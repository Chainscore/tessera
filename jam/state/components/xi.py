from jam.types.base.sequences.array import Array, decodable_array
from jam.types.protocol.core import WorkPackageHash
from jam.utils.constants import EPOCH_LENGTH


@decodable_array(EPOCH_LENGTH, WorkPackageHash)
class Xi(Array[WorkPackageHash]): ...