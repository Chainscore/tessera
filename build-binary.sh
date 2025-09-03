#!/bin/bash
# 🔨 One-Click Binary Builder for Tessera Node
# Builds optimized standalone binaries with all dependencies included

set -e

echo "🔨 Building Tessera Node Binary..."

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

echo "[INFO] Installing dependencies..."
poetry install --only=main

echo "[INFO] Building binary..."
poetry run pyinstaller tessera.spec --clean --noconfirm

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
    
    if [ "$PLATFORM_NAME" = "Darwin" ]; then
        echo "[INFO] "
        echo "[INFO] 📋 To build for Linux:"
        echo "[INFO]   1. Run this script on a Linux machine (Ubuntu/Debian recommended)"
        echo "[INFO]   2. Or use Docker: docker run -it --rm -v \$(pwd):/app ubuntu:22.04 bash"
        echo "[INFO]   3. Then install deps and run: ./build-binary.sh"
    fi
    
else
    echo "[ERROR] ❌ Binary test failed"
    exit 1
fi
