from dataclasses import dataclass
from jam.types.base.choices.choice import Choice, decodable_choice
from jam.types.base.sequences.array import Array, decodable_array
from jam.types.base.sequences.vector import Vector, decodable_vector
from jam.types.extrinsics.tickets import TicketBody
from jam.types.protocol.crypto import BandersnatchPublic, BandersnatchRingRoot, BandersnatchRingVrfSignature
from jam.types.protocol.validators import ValidatorData
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.constants import EPOCH_LENGTH, VALIDATOR_COUNT

@decodable_array(length=VALIDATOR_COUNT, element_type=ValidatorData)
class GammaK(Array[ValidatorData]): 
    """Validator set"""
    ...

@decodable_vector(element_type=TicketBody)
class GammaA(Vector[TicketBody]):
    """Ticket accumulator: set of highest scoring ticket ids to be used for the next epoch"""
    ...
    
GammaZ = BandersnatchRingRoot

@decodable_array(length=EPOCH_LENGTH, element_type=TicketBody)
class GammaSTickets(Array[TicketBody]):
    """Current epoch's slot sealers: set of highest scoring ticket ids for this epoch"""
    ...

@decodable_array(length=EPOCH_LENGTH, element_type=BandersnatchPublic)
class GammaSFallback(Array[BandersnatchPublic]):
    """Fallback set of slot sealers: set of public keys of the slot sealers for this epoch"""
    ...

@decodable_choice
class GammaS(Choice):
    """Either the current epoch's slot sealers or the fallback set of slot sealers"""
    tickets: GammaSTickets
    keys: GammaSFallback


@decodable_dataclass
@dataclass
class Gamma(Codable):
    """Gamma state"""
    k: GammaK
    z: GammaZ
    s: GammaS
    a: GammaA