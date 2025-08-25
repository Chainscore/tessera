from tsrkit_types.bytes import Bytes
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import HeaderHash, StateRoot
from jam.types.protocol.merkle import MMR


class ReportedDictionary(Dictionary[Bytes[32], Bytes[32], "hash", "exports_root"]):
    ...


@structure
class BlockHistory:
    """Block history item"""

    header_hash: HeaderHash
    mmr: MMR
    state_root: StateRoot
    reported: ReportedDictionary

# State key: 3
class Beta(TypedVector[BlockHistory]):
    ...
