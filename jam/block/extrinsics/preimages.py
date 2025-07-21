from jam.block.extrinsics.store import ExtrinsicStore
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.types.protocol.core import ServiceId


@structure
class Preimage:
    """Preimage structure."""

    requester: ServiceId
    blob: Bytes


PreimagesExtrinsic = TypedVector[Preimage]

preimg_store = ExtrinsicStore[Preimage]()
