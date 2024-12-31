from jam.types.base.integers import U16, U32, U64
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = U32
ValidatorIndex = U16
CoreIndex = U16
Gas = U64
ServiceId = U16

# Hash type aliases
WorkPackageHash = OpaqueHash
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash

