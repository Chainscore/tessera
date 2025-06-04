from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
# from jam.types.work.report import WorkReport, WorkDependencies  # Circular import issue
from jam.utils.constants import EPOCH_LENGTH


@structure
class ReadyWR:
    report: object  # WorkReport - temporarily using object to break circular import
    dependencies: object  # WorkDependencies - temporarily using object to break circular import


AllReadyWRs = TypedVector[ReadyWR]

Nu = TypedArray[AllReadyWRs, EPOCH_LENGTH]
