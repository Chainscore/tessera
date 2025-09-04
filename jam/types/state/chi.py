from dataclasses import field

from tsrkit_types.sequences import TypedArray
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.struct import structure
from jam.types.protocol.core import Gas, ServiceId
from jam.utils.constants import CORE_COUNT

"""Index of Manager service that can alter Chi"""
ChiM = ServiceId
"""Can alter Delta"""
ChiA = TypedArray[ServiceId, CORE_COUNT]
"""Can alter Iota"""
ChiV = ServiceId


ChiZ = Dictionary[ServiceId, Gas]

@structure
class Chi:
    """
    Component: χ
    Key: 12

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/121d00121d00?v=0.7.0
    """

    chi_m: ChiM = field(metadata={"name": "bless"})
    chi_a: ChiA = field(metadata={"name": "assign"})
    chi_v: ChiV = field(metadata={"name": "designate"})
    chi_z: ChiZ = field(metadata={"name": "always_acc"})
