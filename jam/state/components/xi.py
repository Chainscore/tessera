from jam.types.base.sequences.array import Array, decodable_array
from jam.types.work.report import WorkDependencies
from jam.utils.constants import EPOCH_LENGTH


@decodable_array(EPOCH_LENGTH, WorkDependencies)
class Xi(Array[WorkDependencies]): ...
