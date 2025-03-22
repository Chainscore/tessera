import os
import platform
from cffi import FFI

class KVStore:
    def __init__(self, path: str):
        self.ffi = FFI()
        self.path = path.encode('utf-8')
        
        # Define C interface
        self.ffi.cdef("""
            typedef struct rocksdb_t rocksdb_t;
            typedef struct rocksdb_options_t rocksdb_options_t;
            typedef struct rocksdb_writeoptions_t rocksdb_writeoptions_t;
            typedef struct rocksdb_readoptions_t rocksdb_readoptions_t;
            
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
                "/opt/homebrew/Cellar/rocksdb/*/lib/librocksdb.dylib"
            ]
        elif system == "Linux":
            lib_names = [
                "librocksdb.so",
                "/usr/lib/librocksdb.so",
                "/usr/local/lib/librocksdb.so"
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
        
        # If we made it here, we couldn't load the library
        raise RuntimeError(f"Couldn't load RocksDB library. Tried:\n" + 
                           "\n".join(errors) + 
                           "\nMake sure librocksdb is installed (brew install rocksdb)")
    
    def _check_error(self, error_ptr):
        error = error_ptr[0]
        if error != self.ffi.NULL:
            error_str = self.ffi.string(error).decode('utf-8')
            self.lib.rocksdb_free(error)
            raise RuntimeError(f"RocksDB error: {error_str}")
    
    def put(self, key: str, value: str):
        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')
        error = self.ffi.new("char**")
        
        self.lib.rocksdb_put(
            self.db, self.woptions,
            key_bytes, len(key_bytes),
            value_bytes, len(value_bytes),
            error
        )
        self._check_error(error)
    
    def get(self, key: str):
        key_bytes = key.encode('utf-8')
        error = self.ffi.new("char**")
        vallen = self.ffi.new("size_t*")
        
        value_ptr = self.lib.rocksdb_get(
            self.db, self.roptions,
            key_bytes, len(key_bytes),
            vallen, error
        )
        self._check_error(error)
        
        if value_ptr == self.ffi.NULL:
            return None
        
        value = self.ffi.string(value_ptr, vallen[0]).decode('utf-8')
        self.lib.rocksdb_free(value_ptr)
        return value
    
    def delete(self, key: str):
        key_bytes = key.encode('utf-8')
        error = self.ffi.new("char**")
        
        self.lib.rocksdb_delete(
            self.db, self.woptions,
            key_bytes, len(key_bytes),
            error
        )
        self._check_error(error)
    
    def close(self):
        if hasattr(self, 'db') and self.db:
            self.lib.rocksdb_close(self.db)
            self.db = None
        
        if hasattr(self, 'options') and self.options:
            self.lib.rocksdb_options_destroy(self.options)
            self.options = None
            
        if hasattr(self, 'woptions') and self.woptions:
            self.lib.rocksdb_writeoptions_destroy(self.woptions)
            self.woptions = None
            
        if hasattr(self, 'roptions') and self.roptions:
            self.lib.rocksdb_readoptions_destroy(self.roptions)
            self.roptions = None
