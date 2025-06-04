from tsrkit_types.sequences import TypedArray
# from jam.types.work.report import WorkDependencies  # Circular import issue
from jam.utils.constants import EPOCH_LENGTH


Xi = TypedArray[object, EPOCH_LENGTH]  # WorkDependencies - temporarily using object to break circular import

