from dataclasses import dataclass
from jam.types.base.dictionary import Dictionary, decodable_dictionary
from jam.types.protocol.core import Gas, ServiceId
from jam.utils.codec.codable import Codable
from jam.utils.codec.decorators.dataclasses import decodable_dataclass
from jam.utils.json import JsonSerde
from jam.utils.json.decorators import with_json_metadata


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

@with_json_metadata(
    chi_m={"name": "bless"},
    chi_a={"name": "assign"},
    chi_v={"name": "designate"},
    chi_g={"name": "always_acc"}
)
@decodable_dataclass
@dataclass
class Chi(Codable, JsonSerde):
    """Chi state"""

    chi_m: ChiM
    chi_a: ChiA
    chi_v: ChiV
    chi_g: ChiG
