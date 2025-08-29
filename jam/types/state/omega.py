from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
from jam.types.work import WorkReport, WorkDependencies
from jam.utils.constants import EPOCH_LENGTH


@structure
class ReadyWR:
    report: WorkReport
    dependencies: WorkDependencies


AllReadyWRs = TypedVector[ReadyWR]

class Omega(TypedArray[AllReadyWRs, EPOCH_LENGTH]):
    """
    Component: ω
    Key: 14

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/16e70016e700?v=0.7.0
    """

    ...
