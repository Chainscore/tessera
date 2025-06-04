from tsrkit_types.integers import Uint
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = Uint[32]  # U32 equivalent
ValidatorIndex = Uint[16]  # U16 equivalent
CoreIndex = Uint[16]  # U16 equivalent
Gas = Uint[64]  # U64 equivalent
RemainingGas = int  # I32 equivalent - using int since Sint doesn't exist
ServiceId = Uint[32]  # U32 equivalent
Balance = Uint[64]  # U64 equivalent
BlobLength = Uint[32]  # U32 equivalent
Register = Uint[64]  # U64 equivalent
ProgramCounter = Uint[64]  # U64 equivalent




# Hash type aliases
WorkPackageHash = OpaqueHash
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash
SegmentRoot = OpaqueHash
