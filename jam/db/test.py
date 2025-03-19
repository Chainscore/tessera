from jam.rocksdb_helper import RocksDBHelper

# Initialize the database (inside 'db' folder)
db = RocksDBHelper()

# Fetch the value
print(db.get(b'user:1'))  # Output: "john_doe"

# Close the database
db.close()
