import plyvel
import os

class RocksDBHelper:
    def __init__(self, db_path=os.path.join(os.path.dirname(__file__), "../my_db")):
        """Initialize and open the RocksDB database inside the 'db' folder"""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)  # Ensure the folder exists
        self.db = plyvel.DB(db_path, create_if_missing=True)

    def put(self, key: str, value: str):
        """Store a key-value pair"""
        self.db.put(key.encode(), value.encode())

    def get(self, key: str):
        """Fetch value for a given key"""
        value = self.db.get(b'user:1')
        return value.decode() if value else None

    def delete(self, key: str):
        """Delete a key-value pair"""
        self.db.delete(key.encode())

    def close(self):
        """Close the database connection"""
        self.db.close()
