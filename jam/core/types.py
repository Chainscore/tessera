# jam/core/types.py

from dataclasses import dataclass
from typing import NewType, Sequence
from enum import Enum

# Basic types
Hash = NewType('Hash', bytes)
PublicKey = NewType('PublicKey', bytes)
Signature = NewType('Signature', bytes)
BlockNumber = NewType('BlockNumber', int)
Slot = NewType('Slot', int)

class ExitReason(Enum):
    NORMAL = 0
    PANIC = 1
    OUT_OF_GAS = 2
    PAGE_FAULT = 3
    HOST_CALL = 4

@dataclass
class CoreAssignment:
    core_id: int
    validator_index: int
    slot: int

@dataclass
class ServiceId:
    index: int

@dataclass
class Balance:
    value: int

    def __add__(self, other: 'Balance') -> 'Balance':
        return Balance(self.value + other.value)

    def __sub__(self, other: 'Balance') -> 'Balance':
        return Balance(self.value - other.value)

# Constants
EPOCH_LENGTH = 600
SLOT_DURATION = 6
VALIDATOR_COUNT = 1023
MAX_SERVICE_CODE_SIZE = 4_000_000
MAX_PREIMAGE_SIZE = 4_000_000