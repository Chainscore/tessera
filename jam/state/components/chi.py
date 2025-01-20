from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.protocol.core import Gas, ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.composite.dataclasses import decodable_dataclass


"""Index of Manager service that can alter Chi"""
ChiM = ServiceId
"""Can alter Delta"""
ChiA = ServiceId
"""Can alter Iota"""
ChiV = ServiceId

@decodable_dictionary(key_type=ServiceId, value_type=Gas)
class ChiG(Dictionary[ServiceId, Gas]):
    """Dictionary containing indices of services which automatically acc in each block w/ basic gas"""
    ...

@decodable_dataclass
@dataclass
class Chi(Codable):
    """Chi state"""
    m: ChiM
    a: ChiA
    v: ChiV
    g: ChiG
