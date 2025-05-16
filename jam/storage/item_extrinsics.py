from typing import List, Tuple

from jam.config.data_stores import main_db
from jam.storage.db.kv import KVStore
from jam.types.base.integers import U32
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.types.work.item import ExtrinsicSpecs, ExtrinsicSpec
from jam.types.work.package import WorkPackage


class ItemExtrinsics:
    """Place to store and get extrinsics that are received along with Work Package"""
    DB = main_db


    @classmethod
    def store(cls, package: WorkPackage, data: List[Bytes]):
        """
        Stores the extrinsic data, decoded as per work items and extrinsic lengths we get from WP

        Args:
            package (WorkPackage): Relevent WP
            data ([Bytes]): Extrinsic data we receive with WP, seperated by Work Item

        Raises:
            ValueError: If the extrinsic passed (to store) is invalid - i.e hashes/length dont match 
        """
        to_store = {}
        # Validation process
        for i, item in enumerate(package.items):
            offset = 0
            item_x_encoded = data[i]
            for extrinsic in item.extrinsic:
                if offset+extrinsic.len > len(item_x_encoded):
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                value = item_x_encoded[offset: offset+extrinsic.len]
                if Hash.blake2b(value) != extrinsic.hash:
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                offset += int(extrinsic.len)
                to_store[extrinsic.hash] = value
            if offset != len(item_x_encoded):
                raise ValueError("Invalid WP: Extrinsic data mismatch")
        
        # Storing data
        for key, value in to_store.items():
            cls.DB.put(bytes(key), bytes(value))


    @classmethod
    def encode(cls, wi_data: List[Bytes]) -> (Bytes, ExtrinsicSpecs):
        """
        Encode a bundle of work item extrinsics to extrinsic bytes and ExtrinsicSpecs
        Args:
            - wi_data: List of extrinsics of a work item
        Returns:
            - extrinsic bytes of this work item
            - extrinsic spec of this work item
        """
        extr_specs = ExtrinsicSpecs([])
        wi = b""
        for ex_data in wi_data:
            extr_specs.append(ExtrinsicSpec(hash=Hash.blake2b(ex_data), len=U32(len(ex_data))))
            wi += ex_data
        return wi, extr_specs


    @classmethod
    def get(cls, extrinsic_hash: ByteArray32) -> bytes:
        """Gets the relevent extrinsic, assuming we already know its hash (as its stored in WI)

        Args:
            extrinsic_hash (ByteArray32)
            db (KVStore)

        Returns:
            Bytes
        """
        return cls.DB.get(bytes(extrinsic_hash))


    @classmethod
    def get_all(cls, wp: WorkPackage) -> List[List[bytes]]:
        result = []
        for item in wp.items:
            item_extr = []
            for extrinsics in item.extrinsic:
                ext = cls.get(extrinsics.hash)
                if len(ext) != extrinsics.len:
                    raise ValueError("Critical: Invalid extrinsic!")
                item_extr.append(ext)
            result.append(item_extr)
        return result