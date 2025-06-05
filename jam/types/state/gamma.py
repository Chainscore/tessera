from dataclasses import field

from tsrkit_types.choice import Choice
from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT


GammaK = TypedArray[ValidatorData, VALIDATOR_COUNT]

GammaA = TypedVector[TicketBody]

GammaZ = BandersnatchRingRoot

GammaSTickets = TypedArray[TicketBody, EPOCH_LENGTH]

GammaSFallback = TypedArray[BandersnatchPublic, EPOCH_LENGTH]


class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""

    tickets: GammaSTickets
    keys: GammaSFallback


@structure
class Gamma:
    """Gamma state"""

    k: GammaK = field(metadata={"name": "gamma_k"})
    z: GammaZ = field(metadata={"name": "gamma_z"})
    s: GammaS = field(metadata={"name": "gamma_s"})
    a: GammaA = field(metadata={"name": "gamma_a"})
