from typing import List, Tuple

from rockstore import RockStore

from jam.types import WorkItem
from jam.types.protocol.crypto import Hash
from jam.types.work import ExtrinsicSpecs, ExtrinsicSpec
from jam.types.work import WorkPackage
from tsrkit_types.bytes import Bytes
from tsrkit_types.integers import U32

from jam.types.work.manifest import MultiExtrinsics, Extrinsic, Extrinsics


class ItemExtrinsics:
    """Place to store and get extrinsics that are received along with Work Package"""

    DB: RockStore

    def __init__(self, db: RockStore):
        self.DB = db

    @classmethod
    def process_item(cls, item: WorkItem, data: Extrinsic) -> Extrinsics:
        ext = Extrinsics([])
        to_store = {}

        offset = 0
        for extrinsic in item.extrinsic:
            if offset + extrinsic.len > len(data):
                raise ValueError("Invalid WP: Extrinsic data mismatch")
            value = data[offset : offset + extrinsic.len]
            if Hash.blake2b(value) != extrinsic.hash:
                raise ValueError("Invalid WP: Extrinsic data mismatch")
            offset += int(extrinsic.len)
            to_store[extrinsic.hash] = value
            ext.append(value)
        if offset != len(data):
            raise ValueError("Invalid WP: Extrinsic data mismatch")

        for key, value in to_store.items():
            cls.DB.put(key.encode(), value.encode())

        return ext

    @classmethod
    def process_package(cls, package: WorkPackage, data: Extrinsics) -> MultiExtrinsics:
        exts = MultiExtrinsics([])
        for i, item in enumerate(package.items):
            item_x_encoded = data[i]
            ext = cls.process_item(item, item_x_encoded)
            exts.append(ext)

        return exts

    @classmethod
    def store_processed(cls, data: MultiExtrinsics):
        for item in data:
            for ext in item:
                key = Hash.blake2b(ext.encode())
                cls.DB.put(key.encode(), ext.encode())

    def store(self, package: WorkPackage, data: List[Bytes]):
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
                if offset + extrinsic.len > len(item_x_encoded):
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                value = item_x_encoded[offset : offset + extrinsic.len]
                if Hash.blake2b(value) != extrinsic.hash:
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                offset += int(extrinsic.len)
                to_store[extrinsic.hash] = value
            if offset != len(item_x_encoded):
                raise ValueError("Invalid WP: Extrinsic data mismatch")

        # Storing data
        for key, value in to_store.items():
            self.DB.put(bytes(key), bytes(value))

    @staticmethod
    def encode(wi_data: List[Bytes]) -> Tuple[Bytes, ExtrinsicSpecs]:
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

    def get(self, extrinsic_hash: Bytes[32]) -> bytes:
        """Gets the relevent extrinsic, assuming we already know its hash (as its stored in WI)

        Args:
            extrinsic_hash (Bytes[32])
            db (RockStore)

        Returns:
            Bytes
        """
        return self.DB.get(bytes(extrinsic_hash))

    def get_all(self, wp: WorkPackage) -> List[List[bytes]]:
        result = []
        for item in wp.items:
            item_extr = []
            for extrinsics in item.extrinsic:
                ext = self.get(extrinsics.hash)
                if len(ext) != extrinsics.len:
                    raise ValueError("Critical: Invalid extrinsic!")
                item_extr.append(ext)
            result.append(item_extr)
        return result
