from jam.db.kv import KVStore
from jam.merklization import BMRFunctions
from jam.types.work.segment import Segments


class SegmentStore:

    db_path = "/home/faizahmad817/tessera/db/segment"
    def __init__(self):
        ...

    def put(self, export_segment: Segments):
        db = KVStore(self.db_path)
        merkle = BMRFunctions()
        print(export_segment)
        e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
        db.put(e.encode(), export_segment.encode())

    def get(self, segment_hash) -> Segments:
        db = KVStore(self.db_path)
        imports = db.get(bytes(segment_hash))
        decoded_imports, _ = Segments.decode_from(imports)
        print(decoded_imports)
        return decoded_imports


from jam.db.kv import KVStore
from jam.merklization import BMRFunctions
from jam.types.work.segment import Segments


class BundleStore:

    db_path = "/home/faizahmad817/tessera/db/bundle"
    def __init__(self):
        ...

    def put(self, export_segment: Segments):
        db = KVStore(self.db_path)
        merkle = BMRFunctions()
        print(export_segment)
        e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
        db.put(e.encode(), export_segment.encode())

    def get(self, segment_hash) -> Segments:
        db = KVStore(self.db_path)
        imports = db.get(bytes(segment_hash))
        decoded_imports, _ = Segments.decode_from(imports)
        print(decoded_imports)
        return decoded_imports