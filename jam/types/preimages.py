"""Preimage types for the JAM protocol."""
from dataclasses import dataclass
from typing import List
from .base import Bits
from .core import ServiceId

@dataclass
class Preimage:
    """Preimage structure."""
    requester: ServiceId
    blob: Bits

@dataclass
class PreimagesExtrinsic:
    """Preimages extrinsic structure."""
    preimages: List[Preimage] 