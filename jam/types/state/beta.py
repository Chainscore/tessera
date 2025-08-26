from tsrkit_types.bytes import Bytes
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import HeaderHash, StateRoot, BeefyRoot
from jam.merklization.mountain_merkle import MMR

ReportedDictionary = Dictionary[Bytes[32], Bytes[32], "hash", "exports_root"]

@structure
class BlockHistory:
    """Block history item"""

    header_hash: HeaderHash
    state_root: StateRoot
    beefy_root: BeefyRoot
    reported: ReportedDictionary

class BetaHistory(TypedVector[BlockHistory]):
    ...

BeefyBelt = MMR

@structure
class Beta:
    h: BetaHistory
    b: BeefyBelt