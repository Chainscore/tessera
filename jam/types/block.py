"""Block and header types for the JAM protocol."""
from dataclasses import dataclass
from typing import List, Optional
from .base import U32
from .core import (
    HeaderHash, StateRoot, OpaqueHash, TimeSlot, ValidatorIndex,
    Entropy, BandersnatchPublic, Ed25519Public
)
from .crypto import BandersnatchVrfSignature
from .tickets import TicketBody, TicketsExtrinsic
from .preimages import PreimagesExtrinsic
from .guarantees import GuaranteesExtrinsic
from .assurances import AssurancesExtrinsic
from .disputes import DisputesExtrinsic

@dataclass
class EpochMark:
    """Epoch mark structure."""
    entropy: Entropy
    tickets_entropy: Entropy
    validators: List[BandersnatchPublic]

@dataclass
class Header:
    """Block header structure."""
    parent: HeaderHash
    parent_state_root: StateRoot
    extrinsic_hash: OpaqueHash
    slot: TimeSlot
    epoch_mark: Optional[EpochMark]
    tickets_mark: Optional[List[TicketBody]]
    offenders_mark: List[Ed25519Public]
    author_index: ValidatorIndex
    entropy_source: BandersnatchVrfSignature
    seal: BandersnatchVrfSignature

@dataclass
class Extrinsic:
    """Block extrinsic structure."""
    tickets: TicketsExtrinsic
    preimages: PreimagesExtrinsic
    guarantees: GuaranteesExtrinsic
    assurances: AssurancesExtrinsic
    disputes: DisputesExtrinsic

@dataclass
class Block:
    """Block structure."""
    header: Header
    extrinsic: Extrinsic

@dataclass
class MmrPeak:
    """MMR peak structure."""
    value: Optional[OpaqueHash]

@dataclass
class Mmr:
    """Merkle Mountain Range structure."""
    peaks: List[MmrPeak]

@dataclass
class ReportedWorkPackage:
    """Reported work package structure."""
    hash: OpaqueHash
    exports_root: OpaqueHash

@dataclass
class BlockInfo:
    """Block information structure."""
    header_hash: HeaderHash
    mmr: Mmr
    state_root: StateRoot
    reported: List[ReportedWorkPackage]

@dataclass
class BlocksHistory:
    """Blocks history structure."""
    blocks: List[BlockInfo]

    def __post_init__(self):
        if len(self.blocks) > 0:  # max_blocks_history should be imported from constants
            raise ValueError("BlocksHistory exceeds maximum allowed blocks") 