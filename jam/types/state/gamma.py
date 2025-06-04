from tsrkit_types.choice import Choice
from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
# from jam.types.extrinsics.tickets import TicketBody  # Circular import issue
from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT


GammaK = TypedArray[ValidatorData, VALIDATOR_COUNT]

GammaA = TypedVector[object]  # TicketBody - temporarily using object to break circular import

GammaZ = BandersnatchRingRoot

GammaSTickets = TypedArray[object, EPOCH_LENGTH]  # TicketBody - temporarily using object to break circular import

GammaSFallback = TypedArray[BandersnatchPublic, EPOCH_LENGTH]


class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""

    tickets: GammaSTickets
    keys: GammaSFallback


@structure
class Gamma:
    """Gamma state"""

    k: GammaK
    z: GammaZ
    s: GammaS
    a: GammaA
