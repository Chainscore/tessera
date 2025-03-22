# Database Module

The `jam.db` module provides database interfaces and implementations for Tessera, focusing on efficient key-value storage solutions.

## Components

### KVStore (RocksDB)

A high-performance key-value store interface using RocksDB, implemented via CFFI (C Foreign Function Interface) for direct access to the RocksDB C API.

#### Features

- Basic key-value operations: put, get, delete
- Full UTF-8 support for keys and values
- Persistent storage with automatic database creation
- Proper resource management and cleanup
- Cross-platform compatibility (macOS, Linux, Windows)

## Requirements

- **RocksDB**: The underlying storage engine
  ```bash
  # macOS
  brew install rocksdb
  
  # Debian/Ubuntu
  apt-get install librocksdb-dev
  
  # Fedora/RHEL
  dnf install rocksdb-devel
  ```

- **Python Dependencies**:
  - cffi: For the C interface

## Usage Examples

### Basic Operations

```python
from jam.db.kv import KVStore

# Initialize a store
db = KVStore("path/to/database")

# Store values
db.put("user:1", "John Doe")
db.put("user:2", "Jane Smith")

# Retrieve values
user1 = db.get("user:1")  # Returns "John Doe"
unknown = db.get("unknown")  # Returns None

# Delete values
db.delete("user:2")

# Always close when done
db.close()
```

## Architecture

The module uses a layered approach:

1. **CFFI Layer**: Directly interfaces with the RocksDB C API
2. **KVStore Class**: Provides a clean Python interface over the C API
3. **Application Layer**: KVStore

## Extending

The database module is designed to be extended with:

- Additional storage backends (e.g., LevelDB, LMDB)
- Higher-level abstractions (e.g., collections, indexes)
- Serialization helpers for complex objects

## Performance Considerations

- RocksDB is optimized for high write throughput
- For read-heavy workloads, consider tweaking RocksDB options
- For large values (>100KB), consider storing references instead of values directly