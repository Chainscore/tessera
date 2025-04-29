import shutil
import tempfile
from jam.merklization import BMRFunctions

from jam.db.kv import KVStore
from jam.types.work.segment import Segments
from tests.dummy.utils import create_dummy_bytes32


def test_put():
    # db_path = tempfile.gettempdir()
    db_path = "db/segment"
    db = KVStore(db_path)
    merkle = BMRFunctions()
    segment = create_dummy_bytes32()
    export_segment = Segments([segment])
    print(export_segment)
    e = BMRFunctions.cd_merkle_fn(merkle, export_segment)
    db.put(e.encode(), export_segment.encode())
    print("stored successfully")
    imports = db.get(bytes(e))
    print("fetched imports: ", imports)
    decoded_imports, _ = Segments.decode_from(imports)
    print(decoded_imports)
    # shutil.rmtree(db_path)
