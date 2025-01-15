
from dataclasses import dataclass
from jam.types.base.choice import Choice, decodable_choice
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchRingRoot, BandersnatchRingVrfSignature
from jam.types.protocol.validators import ValidatorData
from jam.utils.codec.base import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT

@decodable_array(VALIDATOR_COUNT, ValidatorData)
class GammaK(Array[ValidatorData]): 
    """Validator set"""
    ...

@decodable_vector(BandersnatchRingVrfSignature)
class GammaA(Vector[BandersnatchRingVrfSignature]):
    """Ticket accumulator: set of highest scoring ticket ids to be used for the next epoch"""
    ...

GammaZ = BandersnatchRingRoot

@decodable_array(EPOCH_LENGTH, BandersnatchRingVrfSignature)
class GammaSTickets(Array[BandersnatchRingVrfSignature]):
    """Current epoch's slot sealers: set of highest scoring ticket ids for this epoch"""
    ...

@decodable_array(EPOCH_LENGTH, BandersnatchPublic)
class GammaSFallback(Array[BandersnatchPublic]):
    """Fallback set of slot sealers: set of public keys of the slot sealers for this epoch"""
    ...

@decodable_choice([GammaSTickets, GammaSFallback])
class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""
    ...

@decodable_dataclass
@dataclass
class Gamma(Codable):
    """Gamma state"""
    k: GammaK
    z: GammaZ
    s: GammaS
    a: GammaA