from dataclasses import field
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from jam.types.protocol.core import Gas, ServiceId


"""Index of Manager service that can alter Chi"""
ChiM = ServiceId
"""Can alter Delta"""
ChiA = ServiceId
"""Can alter Iota"""
ChiV = ServiceId


ChiG = Dictionary[ServiceId, Gas]


@structure
class Chi:
    """Chi state"""

    chi_m: ChiM = field(metadata={"name": "bless"})
    chi_a: ChiA = field(metadata={"name": "assign"})
    chi_v: ChiV = field(metadata={"name": "designate"})
    chi_g: ChiG = field(metadata={"name": "always_acc"})
