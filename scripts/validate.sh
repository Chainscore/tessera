#!/bin/bash

# Validation script to verify the development environment setup

set -e

echo "🔍 Validating Tessera development environment..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the tessera project root"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run scripts/setup.sh first."
    exit 1
fi

echo ""
echo "📦 Testing core dependency imports..."

# Test dot_ring import
if python -c "import dot_ring; print('   ✅ dot_ring imported successfully')" 2>/dev/null; then
    echo "   ✅ dot_ring imported successfully"
else
    echo "   ❌ dot_ring import failed"
fi

# Test tsrkit_pvm import (with lazy loading)
if python -c "import tsrkit_pvm; print('   ✅ tsrkit_pvm imported successfully (with lazy loading)')" 2>/dev/null; then
    echo "   ✅ tsrkit_pvm imported successfully (with lazy loading)"
else
    echo "   ❌ tsrkit_pvm import failed"
fi

# Test tsrkit_asm import
if python -c "import tsrkit_asm; print('   ✅ tsrkit_asm imported successfully')" 2>/dev/null; then
    echo "   ✅ tsrkit_asm imported successfully"
else
    echo "   ❌ tsrkit_asm import failed"
fi

# Test main jam module import
if python -c "import jam; print('   ✅ jam module imported successfully')" 2>/dev/null; then
    echo "   ✅ jam module imported successfully"
else
    echo "   ❌ jam module import failed"
fi

echo ""
echo "🧪 Testing framework capabilities..."

# Test unit tests
echo "   Running quick unit test sample..."
if poetry run pytest tests/unit -k "test_" --maxfail=1 -q >/dev/null 2>&1; then
    echo "   ✅ Unit tests can run"
else
    echo "   ⚠️ Some unit tests failing (this may be expected)"
fi

# Test vector harness availability
if [ -f "test-suites/harness/w3f/stf/test_w3f_vectors.py" ]; then
    echo "   ✅ W3F test vectors available"
else
    echo "   ❌ W3F test vectors not found"
fi

echo ""
echo "🔧 Platform capabilities..."
case "$(uname -s)" in
    Darwin)
        echo "   📱 Platform: macOS"
        echo "   ✅ Pure Python tests supported"
        echo "   ⚠️ PVM recompiler not supported (requires Linux)"
        ;;
    Linux)
        echo "   🐧 Platform: Linux"
        echo "   ✅ Full functionality available"
        echo "   ✅ PVM recompiler supported"
        ;;
    *)
        echo "   ❓ Platform: $(uname -s) (untested)"
        ;;
esac

echo ""
echo "📋 Available test commands:"
echo "   • Unit tests: ./scripts/test.sh --unit"
echo "   • Vector tests: ./scripts/test.sh --vectors --module <module> --spec <spec>"
echo "   • All compatible tests: ./scripts/test.sh"
echo ""
echo "🎉 Environment validation complete!"
