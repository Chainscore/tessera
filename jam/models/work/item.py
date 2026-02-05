"""Work item types for the JAM protocol."""
from dataclasses import fields
from typing import Union, Tuple

from tsrkit_types.integers import Uint, U16
from tsrkit_types.bytes import Bytes
from tsrkit_types.sequences import TypedVector
from tsrkit_types.struct import structure

from jam.models import WorkPackageHash
from jam.models.protocol.core import Gas, ServiceId, SegmentRoot
from jam.models.protocol.crypto import OpaqueHash

TreeRoot = Union[SegmentRoot, WorkPackageHash]

@structure
class ImportSpec:
    """Import specification structure."""

    tree_root: TreeRoot
    index: Uint[16]

    def encode_into(self, buffer: bytearray, offset: int = 0) -> int:
        if isinstance(self.tree_root, SegmentRoot):
            index = self.index
        elif isinstance(self.tree_root, WorkPackageHash):
            index = U16(self.index + 2 ** 15)
        else:
            raise ValueError(f"Unidentified Tree Root {type(self.tree_root)}")

        current_offset = offset

        items = [self.tree_root, index]
        for item in items:
            size = item.encode_into(buffer, current_offset)
            current_offset += size

        return current_offset - offset

    @classmethod
    def from_json(cls, data: dict) -> "ImportSpec":
        init_data = {}
        for field in fields(cls):
            k = field.metadata.get("name", field.name)
            v = data.get(k)

            f_type = field.type
            if field.name == "tree_root":
                f_type = OpaqueHash

            init_data[field.name] = f_type.from_json(v)

        return cls(**init_data)

    @classmethod
    def decode_from(
            cls, buffer: Union[bytes, bytearray, memoryview], offset: int = 0
    ) -> Tuple["ImportSpec", int]:
        index = U16.decode(buffer[offset+32:offset+34])
        if index < (2 ** 15):
            sr_root = SegmentRoot(buffer[offset:offset+32])
            return cls(
                tree_root=sr_root,
                index=index
            ), offset + 34
        else:
            wp_hash = WorkPackageHash.decode(buffer[offset:offset+32])
            return cls(
                tree_root=wp_hash,
                index=U16(index - 2**15)
            ), offset + 34

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