from jam.db.kv import KVStore
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.types.work.package import WorkPackage


class ItemExtrinsics:
    """Place to store and get extrinsics that are received along with Work Package"""

    @classmethod
    def store(cls, package: WorkPackage, data: Bytes, db: KVStore):
        """Stores the extrinsic data, decoded as per work items and extrinsic lengths we get from WP

        Args:
            package (WorkPackage): Relevent WP
            data (Bytes): Extrinsic data we receive with WP
            db (KVStore): Data store

        Raises:
            ValueError: If the extrinsic passed (to store) is invalid - i.e hashes/length dont match 
        """
        offset = 0
        to_store = {}
        # Validation process
        for item in package.items:
            for extrinsic in item.extrinsic:
                if offset+extrinsic.len > len(data):
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                value = data[offset: offset+extrinsic.len]
                if Hash.blake2b(value) != extrinsic.hash:
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                offset += int(extrinsic.len)
                to_store[extrinsic.hash] = value
        if offset != len(data):
            raise ValueError("Invalid WP: Extrinsic data mismatch")
        
        # Storing data
        for key, value in to_store.items():
            db.put(bytes(key), bytes(value))

    @classmethod
    def get(cls, extrinsic_hash: ByteArray32, db: KVStore) -> bytes:
        """Gets the relevent extrinsic, assuming we already know its hash (as its stored in WI)

        Args:
            extrinsic_hash (ByteArray32)
            db (KVStore)

        Returns:
            Bytes
        """
        return db.get(bytes(extrinsic_hash))
