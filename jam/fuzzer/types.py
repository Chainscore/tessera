"""Fuzzer message types implementing the JAM Fuzzing Protocol v1.

This module contains types that match the ASN.1 schema defined in fuzz-v1.asn.
Uses tsrkit-types for automatic encode/decode functionality.
"""
from tsrkit_types import Bytes, Bytes32, U8, U16, U32, TypedVector, String, structure

from jam.block.header import Header
from jam.block.block import Block


@structure
class Version:
    """Version ::= SEQUENCE { major U8, minor U8, patch U8 }"""
    major: U8
    minor: U8  
    patch: U8


@structure  
class PeerInfo:
    """PeerInfo ::= SEQUENCE {
        fuzz-version  U8,
        fuzz-features Features,  
        jam-version   Version,
        app-version   Version,
        app-name      UTF8String
    }"""
    fuzz_version: U8
    fuzz_features: U32   # Features = U32
    jam_version: Version
    app_version: Version  
    app_name: String


@structure
class KeyValue:
    """KeyValue ::= SEQUENCE {
        key     OCTET STRING (SIZE(31)),
        value   OCTET STRING
    }"""
    key: Bytes[31]     # Will be constrained to 31 bytes at runtime
    value: Bytes


@structure
class State:
    """State ::= SEQUENCE OF KeyValue"""
    keyvals: TypedVector[KeyValue]


@structure
class AncestryItem:
    """AncestryItem ::= SEQUENCE {
        slot TimeSlot,
        header-hash HeaderHash  
    }"""
    slot: U32        # TimeSlot = U32
    header_hash: Bytes32  # HeaderHash = Hash = 32 bytes


@structure
class Ancestry:
    """Ancestry ::= SEQUENCE (SIZE(0..24)) OF AncestryItem
    
    Note: Max size constraint handled at application level
    """
    items: TypedVector[AncestryItem]


@structure
class Initialize:
    """Initialize ::= SEQUENCE {
        header Header,
        keyvals State,
        ancestry Ancestry
    }"""
    header: Header
    keyvals: State
    ancestry: Ancestry


@structure
class ErrorMessage:
    """Error ::= UTF8String"""
    message: String


# Keep old aliases for compatibility during transition
KeyVal = KeyValue
SetStateData = Initialize  # Old name mapping

__all__ = [
    "Version", "PeerInfo", "KeyValue", "KeyVal", "State", 
    "AncestryItem", "Ancestry", "Initialize", "ErrorMessage",
    "SetStateData"  # Legacy alias
]
