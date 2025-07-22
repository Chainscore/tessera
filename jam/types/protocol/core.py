from tsrkit_types.integers import Uint
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = Uint[32]
TrancheIndex = Uint[8]
ValidatorIndex = Uint[16]
CoreIndex = Uint[16]
EpochIndex = Uint[32]
Gas = Uint[64]
RemainingGas = int
ServiceId = Uint[32]
Balance = Uint[64]
BlobLength = Uint[32]
Register = Uint[64]
ProgramCounter = Uint[64]


# Hash type aliases
WorkPackageHash = OpaqueHash
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash
SegmentRoot = OpaqueHash
