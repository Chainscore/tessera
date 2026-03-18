from typing import TYPE_CHECKING

from tsrkit_types.integers import Uint
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = Uint[32]

if TYPE_CHECKING:
    from jam.jam_node import JamNode


class ValidatorIndex(Uint[16]):
    @classmethod
    def from_bandersnatch(cls, jam: "JamNode"):
        """
        Get block producer's author index from the state
        """
        logger = jam.logger
        state = jam.state
        settings = jam.settings

        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == settings.bandersnatch_public:
                return ValidatorIndex(i)

        logger.error(
            "Author not found in validator set",
            our_key=settings.bandersnatch_public,
        )
        raise ValueError("Author not found in the state")


CoreIndex = Uint[16]
EpochIndex = Uint[32]
TrancheIndex = Uint[8]
Gas = Uint[64]
RemainingGas = int
ServiceId = Uint[32]
Balance = Uint[64]
BlobLength = Uint[32]
Register = Uint[64]
ProgramCounter = Uint[64]


# Hash type aliases
class WorkPackageHash(OpaqueHash): ...
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash
class SegmentRoot(OpaqueHash): ...
