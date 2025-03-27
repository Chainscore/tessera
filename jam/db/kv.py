import os
import platform
from cffi import FFI

class KVStore:
    """
    Key-Value Store using RocksDB
    Args:
        path (str): The path to the database file

    Raises:
        RuntimeError: If the RocksDB library cannot be loaded

    Example:
        >>> db = KVStore("db")
        >>> db.put(b"key", b"value")
        >>> print(db.get(b"key"))
        b"value"
    """
    def __init__(self, path: str):
        self.ffi = FFI()
        self.path = path.encode("utf-8")

        # Define C interface
        self.ffi.cdef("""
            typedef struct rocksdb_t rocksdb_t;
            typedef struct rocksdb_options_t rocksdb_options_t;
            typedef struct rocksdb_writeoptions_t rocksdb_writeoptions_t;
            typedef struct rocksdb_readoptions_t rocksdb_readoptions_t;
            typedef struct rocksdb_iterator_t rocksdb_iterator_t;
            
            rocksdb_options_t* rocksdb_options_create();
            void rocksdb_options_set_create_if_missing(rocksdb_options_t*, unsigned char);
            void rocksdb_options_destroy(rocksdb_options_t*);
            
            rocksdb_t* rocksdb_open(rocksdb_options_t* options, const char* name, char** errptr);
            void rocksdb_close(rocksdb_t*);
            
            rocksdb_writeoptions_t* rocksdb_writeoptions_create();
            void rocksdb_writeoptions_destroy(rocksdb_writeoptions_t*);
            
            rocksdb_readoptions_t* rocksdb_readoptions_create();
            void rocksdb_readoptions_destroy(rocksdb_readoptions_t*);
            
            void rocksdb_put(rocksdb_t*, const rocksdb_writeoptions_t*,
                           const char* key, size_t keylen,
                           const char* val, size_t vallen,
                           char** errptr);
                           
            char* rocksdb_get(rocksdb_t*, const rocksdb_readoptions_t*,
                            const char* key, size_t keylen,
                            size_t* vallen, char** errptr);
                            
            void rocksdb_delete(rocksdb_t*, const rocksdb_writeoptions_t*,
                              const char* key, size_t keylen, char** errptr);
            
            // Iterator functions for get_all method
            rocksdb_iterator_t* rocksdb_create_iterator(
                rocksdb_t* db, const rocksdb_readoptions_t* options);
            void rocksdb_iter_destroy(rocksdb_iterator_t* iterator);
            unsigned char rocksdb_iter_valid(const rocksdb_iterator_t* iterator);
            void rocksdb_iter_seek_to_first(rocksdb_iterator_t* iterator);
            void rocksdb_iter_next(rocksdb_iterator_t* iterator);
            const char* rocksdb_iter_key(const rocksdb_iterator_t* iterator, size_t* keylen);
            const char* rocksdb_iter_value(const rocksdb_iterator_t* iterator, size_t* vallen);
            
            void rocksdb_free(void* ptr);
        """)

        # Load the RocksDB library with various path options
        self._load_library()

        # Create options
        self.options = self.lib.rocksdb_options_create()
        self.lib.rocksdb_options_set_create_if_missing(self.options, 1)

        # Open database
        error = self.ffi.new("char**")
        self.db = self.lib.rocksdb_open(self.options, self.path, error)
        self._check_error(error)

        # Create read/write options
        self.woptions = self.lib.rocksdb_writeoptions_create()
        self.roptions = self.lib.rocksdb_readoptions_create()

    def _load_library(self):
        """Try multiple ways to load the RocksDB library."""
        system = platform.system()
        errors = []

        # Common library name by system
        if system == "Darwin":  # macOS
            lib_names = [
                "librocksdb.dylib",
                "/usr/local/lib/librocksdb.dylib",
                "/opt/homebrew/lib/librocksdb.dylib",
                "/usr/local/Cellar/rocksdb/*/lib/librocksdb.dylib",
                "/opt/homebrew/Cellar/rocksdb/*/lib/librocksdb.dylib",
            ]
        elif system == "Linux":
            lib_names = [
                "librocksdb.so",
                "/usr/lib/librocksdb.so",
                "/usr/lib64/librocksdb.so",  # Fedora commonly uses lib64
                "/usr/lib64/librocksdb.so.*",  # Versioned libraries in Fedora
                "/usr/local/lib/librocksdb.so",
                "/usr/local/lib64/librocksdb.so",
            ]
        else:  # Windows or other
            lib_names = ["rocksdb.dll"]

        # Try to load from paths with wildcard expansion
        for lib_name in lib_names:
            if "*" in lib_name:
                import glob

                matching_libs = glob.glob(lib_name)
                for lib in matching_libs:
                    try:
                        self.lib = self.ffi.dlopen(lib)
                        return
                    except OSError as e:
                        errors.append(f"Failed to load {lib}: {str(e)}")
            else:
                try:
                    self.lib = self.ffi.dlopen(lib_name)
                    return
                except OSError as e:
                    errors.append(f"Failed to load {lib_name}: {str(e)}")

        # Provide better installation instructions for Fedora
        install_instructions = ""
        if system == "Linux" and os.path.exists("/etc/fedora-release"):
            install_instructions = "\nInstall RocksDB on Fedora with: sudo dnf install rocksdb rocksdb-devel"
        elif system == "Linux" and os.path.exists("/etc/debian_version"):
            install_instructions = "\nInstall RocksDB on Debian/Ubuntu with: sudo apt-get install librocksdb-dev"
        elif system == "Darwin":
            install_instructions = (
                "\nInstall RocksDB on macOS with: brew install rocksdb"
            )

        # If we made it here, we couldn't load the library
        raise RuntimeError(
            "Couldn't load RocksDB library. Tried:\n"
            + "\n".join(errors)
            + f"{install_instructions}"
        )

    def _check_error(self, error_ptr):
        error = error_ptr[0]
        if error != self.ffi.NULL:
            error_str = self.ffi.string(error).decode("utf-8")
            self.lib.rocksdb_free(error)
            raise RuntimeError(f"RocksDB error: {error_str}")

    def put(self, key_bytes: bytes, value_bytes: bytes):
        error = self.ffi.new("char**")

        self.lib.rocksdb_put(
            self.db,
            self.woptions,
            key_bytes,
            len(key_bytes),
            value_bytes,
            len(value_bytes),
            error,
        )
        self._check_error(error)

    def get(self, key_bytes: bytes):
        error = self.ffi.new("char**")
        vallen = self.ffi.new("size_t*")

        value_ptr = self.lib.rocksdb_get(
            self.db, self.roptions, key_bytes, len(key_bytes), vallen, error
        )
        self._check_error(error)

        if value_ptr == self.ffi.NULL:
            return None

        value = self.ffi.string(value_ptr, vallen[0]).decode("utf-8")
        self.lib.rocksdb_free(value_ptr)
        return value

    def get_all(self):
        """
        Retrieve all key-value pairs from the database.

        Returns:
            dict: Dictionary of all keys and values.
        """
        result = {}

        # Create an iterator
        iterator = self.lib.rocksdb_create_iterator(self.db, self.roptions)

        # Seek to the first element
        self.lib.rocksdb_iter_seek_to_first(iterator)

        # Iterate through all elements
        keylen = self.ffi.new("size_t*")
        vallen = self.ffi.new("size_t*")

        while self.lib.rocksdb_iter_valid(iterator) == 1:
            # Get key and value
            key_ptr = self.lib.rocksdb_iter_key(iterator, keylen)
            value_ptr = self.lib.rocksdb_iter_value(iterator, vallen)

            # Convert to Python bytes
            key = bytes(self.ffi.buffer(key_ptr, keylen[0]))
            value = bytes(self.ffi.buffer(value_ptr, vallen[0]))

            # Store in result dictionary
            result[key] = value

            # Move to next entry
            self.lib.rocksdb_iter_next(iterator)

        # Clean up the iterator
        self.lib.rocksdb_iter_destroy(iterator)

        return result

    def delete(self, key_bytes: bytes):
        error = self.ffi.new("char**")

        self.lib.rocksdb_delete(
            self.db, self.woptions, key_bytes, len(key_bytes), error
        )
        self._check_error(error)

    def close(self):
        if hasattr(self, "db") and self.db:
            self.lib.rocksdb_close(self.db)
            self.db = None

        if hasattr(self, "options") and self.options:
            self.lib.rocksdb_options_destroy(self.options)
            self.options = None

        if hasattr(self, "woptions") and self.woptions:
            self.lib.rocksdb_writeoptions_destroy(self.woptions)
            self.woptions = None

        if hasattr(self, "roptions") and self.roptions:
            self.lib.rocksdb_readoptions_destroy(self.roptions)
            self.roptions = None