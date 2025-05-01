from jam.db.kv import KVStore
from jam.types.base.sequences.bytes.byte_array import ByteArray32
from jam.types.base.sequences.bytes.bytes import Bytes
from jam.types.protocol.crypto import Hash
from jam.types.work.package import WorkPackage


class ItemExtrinsics:
    @classmethod
    def store(cls, package: WorkPackage, data: Bytes, db: KVStore):
        offset = 0
        for item in package.items:
            for extrinsic in item.extrinsic:
                value = data[offset: offset+extrinsic.len]
                print("val", value)
                if Hash.blake2b(value) != extrinsic.hash:
                    raise ValueError("Invalid WP: Extrinsic data mismatch")
                db.put(bytes(extrinsic.hash), bytes(value))
                offset += int(extrinsic.len)

    @classmethod
    def get(cls, extrinsic_hash: ByteArray32, db: KVStore) -> Bytes:
        return db.get(bytes(extrinsic_hash))
