from dataclasses import field

from tsrkit_types.choice import Choice
from tsrkit_types.sequences import TypedArray, TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.ticket import TicketBody
from jam.types.protocol.crypto import (
    BandersnatchPublic,
    BandersnatchRingRoot,
)
from jam.types.protocol.validators import ValidatorData
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT


class GammaK(TypedArray[ValidatorData, VALIDATOR_COUNT]):
    ...


class GammaA(TypedVector[TicketBody]):
    ...


GammaZ = BandersnatchRingRoot


class GammaSTickets(TypedArray[TicketBody, EPOCH_LENGTH]):
    ...


class GammaSFallback(TypedArray[BandersnatchPublic, EPOCH_LENGTH]):
    ...


class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""

    tickets: GammaSTickets
    keys: GammaSFallback


# State key: 4
@structure
class Gamma:
    """Gamma state"""

    k: GammaK = field(metadata={"name": "gamma_k"})
    z: GammaZ = field(metadata={"name": "gamma_z"})
    s: GammaS = field(metadata={"name": "gamma_s"})
    a: GammaA = field(metadata={"name": "gamma_a"})
