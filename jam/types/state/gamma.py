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


class GammaP(TypedArray[ValidatorData, VALIDATOR_COUNT]):
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


@structure
class Gamma:
    """
    Component: γ
    Key: 4

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/0ddb000ddb00?v=0.7.0
    """

    p: GammaP = field(metadata={"name": "gamma_k"})
    z: GammaZ = field(metadata={"name": "gamma_z"})
    s: GammaS = field(metadata={"name": "gamma_s"})
    a: GammaA = field(metadata={"name": "gamma_a"})
