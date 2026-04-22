#!/bin/bash
set -e

PLATFORM=$(uname -s)
PROJECT_ROOT=$(pwd)
LIBS_DIR="$PROJECT_ROOT/libs"

echo "Setting up RocksDB library for PyInstaller..."
echo "[INFO] Platform: $PLATFORM"
echo "[INFO] Project root: $PROJECT_ROOT"

# Create libs directory
mkdir -p "$LIBS_DIR"

if [ "$PLATFORM" = "Darwin" ]; then
    echo "[INFO] Setting up for macOS..."
    
    # Try different locations where RocksDB might be installed on macOS
    ROCKSDB_PATHS=(
        "/opt/homebrew/lib/librocksdb.dylib"
        "/usr/local/lib/librocksdb.dylib"
        "/opt/homebrew/Cellar/rocksdb/*/lib/librocksdb.dylib"
        "/usr/local/Cellar/rocksdb/*/lib/librocksdb.dylib"
    )
    
    FOUND_LIB=""
    for path in "${ROCKSDB_PATHS[@]}"; do
        if [[ "$path" == *"*"* ]]; then
            # Handle glob patterns
            for lib in $path; do
                if [ -f "$lib" ]; then
                    FOUND_LIB="$lib"
                    break 2
                fi
            done
        elif [ -f "$path" ]; then
            FOUND_LIB="$path"
            break
        fi
    done
    
    if [ -n "$FOUND_LIB" ]; then
        echo "[INFO] Found RocksDB library at: $FOUND_LIB"
        cp "$FOUND_LIB" "$LIBS_DIR/librocksdb.dylib"
        echo "[INFO] Copied librocksdb.dylib to $LIBS_DIR/"
    else
        echo "[ERROR] ❌ RocksDB library not found!"
        echo "[ERROR] Please install RocksDB with: brew install rocksdb"
        exit 1
    fi
    
elif [ "$PLATFORM" = "Linux" ]; then
    echo "[INFO] Setting up for Linux..."
    
    # Try different locations where RocksDB might be installed on Linux
    ROCKSDB_PATHS=(
        "/usr/lib/x86_64-linux-gnu/librocksdb.so"
        "/usr/lib64/librocksdb.so"
        "/usr/lib/librocksdb.so"
        "/usr/local/lib/librocksdb.so"
        "/usr/local/lib64/librocksdb.so"
    )
    
    # Also try versioned libraries and pick the newest
    VERSIONED_PATHS=(
        "/usr/lib/x86_64-linux-gnu/librocksdb.so.*"
        "/usr/lib64/librocksdb.so.*"
        "/usr/lib/librocksdb.so.*"
        "/usr/local/lib/librocksdb.so.*"
        "/usr/local/lib64/librocksdb.so.*"
    )
    
    FOUND_LIB=""
    # First try exact matches
    for path in "${ROCKSDB_PATHS[@]}"; do
        if [ -f "$path" ]; then
            FOUND_LIB="$path"
            break
        fi
    done
    
    # If no exact match, try versioned libraries
    if [ -z "$FOUND_LIB" ]; then
        for pattern in "${VERSIONED_PATHS[@]}"; do
            for lib in $pattern; do
                if [ -f "$lib" ]; then
                    FOUND_LIB="$lib"
                    break 2
                fi
            done
        done
    fi
    
    if [ -n "$FOUND_LIB" ]; then
        echo "[INFO] Found RocksDB library at: $FOUND_LIB"
        cp "$FOUND_LIB" "$LIBS_DIR/librocksdb.so"
        echo "[INFO] Copied librocksdb.so to $LIBS_DIR/"
    else
        echo "[ERROR] ❌ RocksDB library not found!"
        echo "[ERROR] Please install RocksDB with:"
        echo "[ERROR]   Debian/Ubuntu: sudo apt-get install librocksdb-dev"
        echo "[ERROR]   Fedora/RHEL:   sudo dnf install rocksdb rocksdb-devel"
        exit 1
    fi
    
else
    echo "[ERROR] ❌ Unsupported platform: $PLATFORM"
    echo "[ERROR] This script supports Linux and macOS only."
    exit 1
fi

echo "[INFO] RocksDB library setup complete!"
echo "[INFO] Library location: $LIBS_DIR/"
echo "[INFO] PyInstaller will now bundle this library in the binary."
