from jam.types.base.integers import U16, U32, U64
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = U32
ValidatorIndex = U16
CoreIndex = U16
Gas = U64
ServiceId = U32
Balance = U64
BlobLength = U32
Register = U64

# Hash type aliases
WorkPackageHash = OpaqueHash
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash
SegmentRoot = OpaqueHash
