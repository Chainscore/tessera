"""Work item types for the JAM protocol."""
from typing import Union, Tuple

from tsrkit_types.integers import Uint, U16
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.types import WorkPackageHash
from jam.types.protocol.core import Gas, ServiceId, SegmentRoot
from jam.types.protocol.crypto import OpaqueHash

TreeRoot = Union[SegmentRoot, WorkPackageHash]

@structure
class ImportSpec:
    """Import specification structure."""

    tree_root: TreeRoot
    index: Uint[16]

    def encode(self):
        if isinstance(self.tree_root, SegmentRoot):
            return self.tree_root.encode() + self.index.encode()
        elif isinstance(self.tree_root, WorkPackageHash):
            return self.tree_root.encode() + U16(self.index + 2 ** 15).encode()
        else:
            raise ValueError(f"Unidentified Tree Root {type(self.tree_root)}")

    @classmethod
    def decode_from(
            cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple["ImportSpec", int]:

        index = U16.decode(buffer[32:34])
        if index < (2 ** 15):
            sr_root = SegmentRoot.decode(buffer[:2])
            return cls(
                tree_root=sr_root,
                index=index
            )
        else:
            wp_hash = WorkPackageHash.decode(buffer[:2])
            return cls(
                tree_root=wp_hash,
                index=U16(index - 2**15)
            )

@structure
class ExtrinsicSpec:
    """Extrinsic specification structure."""

    hash: OpaqueHash
    len: Uint[32]


ImportSpecs = TypedVector[ImportSpec]

ExtrinsicSpecs = TypedVector[ExtrinsicSpec]


@structure
class WorkItem:
    """
    Set W
    Work item structure.

    Source: https://graypaper.fluffylabs.dev/#/38c4e62/1ab0001ae900?v=0.7.0
    """

    # s
    service: ServiceId
    # c
    code_hash: OpaqueHash
    # g
    refine_gas_limit: Gas
    # a
    accumulate_gas_limit: Gas
    # e
    export_count: Uint[16]
    # y
    payload: Bytes
    # i
    import_segments: ImportSpecs
    # x
    extrinsic: ExtrinsicSpecs
