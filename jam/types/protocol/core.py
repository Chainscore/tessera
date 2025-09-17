from jam.types.protocol.validators import ValidatorsData
from tsrkit_types.integers import Uint
from jam.types.protocol.crypto import OpaqueHash

# Simple type aliases
TimeSlot = Uint[32]


class ValidatorIndex(Uint[16]):
    @classmethod
    def from_bandersnatch(cls, b_key, val_set: ValidatorsData):
        """
        Get block producer's author index from the state
        """
        from jam.network.start import node
        from jam.state.state import state
        from jam.log_setup import node_logger as logger

        for i, validator in enumerate(state.kappa):
            if validator.bandersnatch == node.validator_data.bandersnatch:
                return ValidatorIndex(i)

        logger.error(
            "Author not found in validator set",
            our_key=node.validator_data.bandersnatch,
        )
        raise ValueError("Author not found in the state")


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
class WorkPackageHash(OpaqueHash): ...
WorkReportHash = OpaqueHash
ExportsRoot = OpaqueHash
ErasureRoot = OpaqueHash
class SegmentRoot(OpaqueHash): ...
