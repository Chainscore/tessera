#!/bin/bash

set -e

echo "🔨 Building Tessera Node Binary..."

# Verify critical dependencies are present
echo "[INFO] Verifying dependencies..."
REQUIRED_DEPS=(
    "deps/tsrkit-pvm"
    "deps/py-ark-vrf"
    "deps/rockstore"
    "deps/tsrkit-asm"
    "deps/tsrkit-types"
)

MISSING_DEPS=()
for dep in "${REQUIRED_DEPS[@]}"; do
    if [ ! -d "$dep" ] || [ -z "$(ls -A "$dep" 2>/dev/null)" ]; then
        MISSING_DEPS+=("$dep")
    fi
done

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "❌ ERROR: Missing required dependencies:"
    printf '   %s\n' "${MISSING_DEPS[@]}"
    echo ""
    echo "💡 Please run: git submodule update --init --recursive"
    exit 1
fi
echo "[INFO] ✅ All dependencies present"

# Detect platform
PLATFORM=$(uname -s)
ARCH=$(uname -m)
if [ "$PLATFORM" = "Darwin" ]; then
    PLATFORM_NAME="Darwin"
    [ "$ARCH" = "arm64" ] && ARCH_NAME="arm64" || ARCH_NAME="x64"
elif [ "$PLATFORM" = "Linux" ]; then
    PLATFORM_NAME="Linux"
    [ "$ARCH" = "x86_64" ] && ARCH_NAME="x64" || ARCH_NAME="$ARCH"
else
    echo "❌ Unsupported platform: $PLATFORM"
    exit 1
fi

echo "[INFO] Building for: $PLATFORM_NAME-$ARCH_NAME"
echo "[INFO] Cleaning previous builds..."
rm -rf build/ dist/

# Build all native dependencies with optimizations
echo "[INFO] Building native dependencies with release optimizations..."

# Set up Python environment variables for PyO3/Rust builds
export PYTHON_SYS_EXECUTABLE=$(uv run python -c "import sys; print(sys.executable)")
export PYO3_PYTHON="$PYTHON_SYS_EXECUTABLE"
echo "[INFO] Using Python: $PYTHON_SYS_EXECUTABLE"

# Debug Python environment for PyO3 builds
echo "[INFO] Python debug info:"
uv run python -c "
import sys, sysconfig
print(f'  Python version: {sys.version}')
print(f'  Python executable: {sys.executable}')
print(f'  Python library: {sysconfig.get_config_var(\"LIBDIR\")}')
print(f'  Python include: {sysconfig.get_path(\"include\")}')
"

# Build Rust dependencies with proper Python linking
if [ -d deps/py-ark-vrf ]; then
    cd deps/py-ark-vrf
    echo "[INFO] Building py-ark-vrf (PyO3/Rust) in release mode..."
    
    # Check if maturin is available globally or install it locally
    if ! command -v maturin &> /dev/null && ! uv run --help | grep -q maturin; then
        echo "[INFO] Installing maturin for PyO3 builds..."
        uv add --dev maturin || uv pip install maturin
    fi
    
    # Use maturin for PyO3 projects instead of cargo directly
    echo "[INFO] Building with maturin for proper Python linking..."
    PYO3_PYTHON="$PYTHON_SYS_EXECUTABLE" uv run maturin develop --release
    cd ../..
else
    echo "[WARN] deps/py-ark-vrf not found, skipping"
fi

if [ -d deps/rockstore ]; then
    cd deps/rockstore
    echo "[INFO] Building rockstore (Python package) with optimizations..."
    CFLAGS="-O3 -march=native" uv pip install -e . --force-reinstall
    cd ../..
else
    echo "[WARN] deps/rockstore not found, skipping"
fi

# Build PVM with aggressive optimizations
if [ -d deps/tsrkit-pvm ]; then
    cd deps/tsrkit-pvm
    echo "[INFO] Building tsrkit-pvm with Cython optimizations..."
    CFLAGS="-O3 -march=native -flto" LDFLAGS="-flto" PVM_BUILD_MODE=cython uv run python setup.py build_ext --inplace --force
    cd ../..
else
    echo "[WARN] deps/tsrkit-pvm not found, skipping tsrkit-pvm build"
fi

# Build other native dependencies
if [ -d deps/tsrkit-asm ]; then
    cd deps/tsrkit-asm
    echo "[INFO] Building tsrkit-asm with optimizations..."
    CFLAGS="-O3 -march=native" uv pip install -e . --force-reinstall
    cd ../..
fi

if [ -d deps/tsrkit-types ]; then
    cd deps/tsrkit-types
    echo "[INFO] Building tsrkit-types with optimizations..."
    CFLAGS="-O3 -march=native" uv pip install -e . --force-reinstall
    cd ../..
fi

echo "[INFO] Setting up RocksDB library for bundling..."
./setup-rocksdb.sh

echo "[INFO] Building binary..."
uv run pyinstaller tessera.spec --clean --noconfirm

# Test binary
echo "[INFO] Testing binary..."
if ./dist/tessera-node --help > /dev/null 2>&1; then
    echo "[INFO] ✅ Binary test passed!"
    
    # Show size
    SIZE=$(du -sh dist/tessera-node | cut -f1)
    echo "[INFO] 📏 Binary size: $SIZE"
    
    # Create package
    echo "[INFO] Creating package..."
    cd dist/
    # Copy config files to dist if they exist
    [ -f "../dev-spec.json" ] && cp "../dev-spec.json" .
    [ -d "../envs" ] && cp -r "../envs" .
    tar -czf "tessera-node-${PLATFORM_NAME}-${ARCH_NAME}.tar.gz" tessera-node $([ -f "dev-spec.json" ] && echo "dev-spec.json") $([ -d "envs" ] && echo "envs")
    cd ..
    
    echo "[INFO] ✅ BUILD COMPLETE!"
    echo "[INFO] 📦 Binary: dist/tessera-node"
    echo "[INFO] 📦 Package: dist/tessera-node-${PLATFORM_NAME}-${ARCH_NAME}.tar.gz"
    echo "[INFO] "
    echo "[INFO] Usage:"
    echo "[INFO]   ./dist/tessera-node --help"
    echo "[INFO]   ./dist/tessera-node --port 40000"
    
else
    echo "[ERROR] ❌ Binary test failed"
    exit 1
fi
