from dataclasses import field

from tsrkit_types.bytes import Bytes
from tsrkit_types.dictionary import Dictionary
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure
from jam.types.protocol.crypto import HeaderHash, StateRoot, BeefyRoot
from jam.types.protocol.merkle import MMR

class ReportedDictionary(Dictionary[Bytes[32], Bytes[32], "hash", "exports_root"]):
    ...

@structure
class BlockHistory:
    """Block history item"""

    header_hash: HeaderHash
    beefy_root: BeefyRoot
    state_root: StateRoot
    reported: ReportedDictionary

BetaHistory = TypedVector[BlockHistory]

BeefyBelt = MMR

@structure
class Beta:
    """
    Component: β
    Key: 3

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/0f19020f1902?v=0.7.0
    """
    h: BetaHistory = field(metadata={"name": "history"})
    b: BeefyBelt = field(metadata={"name": "mmr"})
