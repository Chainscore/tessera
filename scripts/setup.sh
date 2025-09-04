#!/bin/bash
# scripts/setup.sh

# Ensure script fails on any error
set -e

echo "🚀 Setting up Tessera development environment..."

# Find the best available Python version
REQUIRED_PYTHON_VERSION="3.12"
PYTHON_EXECUTABLE=""

# Try to find a compatible Python version
for python_cmd in python3.12 python3.13 python3; do
    if command -v "$python_cmd" &> /dev/null; then
        PYTHON_VERSION=$($python_cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        if [ $(echo "$PYTHON_VERSION >= $REQUIRED_PYTHON_VERSION" | bc -l) -eq 1 ]; then
            PYTHON_EXECUTABLE="$python_cmd"
            echo "✅ Found compatible Python: $python_cmd (version $PYTHON_VERSION)"
            break
        else
            echo "⚠️  Found $python_cmd (version $PYTHON_VERSION) but need $REQUIRED_PYTHON_VERSION+"
        fi
    fi
done

if [ -z "$PYTHON_EXECUTABLE" ]; then
    echo "❌ Error: Python $REQUIRED_PYTHON_VERSION or higher is required"
    echo ""
    echo "   Available Python versions:"
    for cmd in python3 python3.11 python3.12 python3.13; do
        if command -v "$cmd" &> /dev/null; then
            version=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' 2>/dev/null || echo "unknown")
            echo "     $cmd: $version"
        fi
    done
    echo ""
    echo "   Please install Python $REQUIRED_PYTHON_VERSION or higher:"
    echo "   - macOS: brew install python@3.12"
    echo "   - Ubuntu/Debian: sudo apt install python3.12"
    echo "   - Or visit: https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with $PYTHON_EXECUTABLE..."
    $PYTHON_EXECUTABLE -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify we're using the right Python in venv
VENV_PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "📍 Virtual environment Python version: $VENV_PYTHON_VERSION"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install poetry if not present
if ! command -v poetry &> /dev/null; then
    echo "📚 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python -
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ Poetry installed"
else
    echo "✅ Poetry already installed"
fi

# Initialize and update submodules
echo "📥 Initializing and updating Git submodules..."
git submodule init
git submodule update --recursive
echo "✅ Submodules updated"

# Build submodule dependencies
echo "🔨 Building submodule dependencies..."

# Build py-ark-vrf if it exists
if [ -d "deps/py-ark-vrf" ]; then
    echo "   Building py-ark-vrf..."
    cd deps/py-ark-vrf
    pip install -e . || echo "   ⚠️ Warning: py-ark-vrf build failed"
    cd ../..
fi

# Install other submodule dependencies as editable
if [ -d "deps/tsrkit-pvm" ]; then
    echo "   Installing tsrkit-pvm as editable..."
    cd deps/tsrkit-pvm
    pip install -e . || echo "   ⚠️ Warning: tsrkit-pvm install failed"
    cd ../..
fi

if [ -d "deps/tsrkit-asm" ]; then
    echo "   Installing tsrkit-asm as editable..."
    cd deps/tsrkit-asm
    pip install -e . || echo "   ⚠️ Warning: tsrkit-asm install failed"
    cd ../..
fi

echo "✅ Submodule dependencies built"

# Configure Poetry to use virtual environment
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.create false
poetry config virtualenvs.in-project false

# Check if poetry.lock needs to be updated
if ! poetry check --lock 2>/dev/null; then
    echo "🔄 Updating poetry.lock file..."
    poetry lock
    echo "✅ Poetry lock file updated"
fi

# Install dependencies
echo "📦 Installing project dependencies..."
poetry install
echo "✅ Dependencies installed"

# Setup test suites if available
if [ -d "test-suites" ]; then
    echo "🧪 Setting up test suites..."
    cd test-suites
    
    # Initialize test suites submodules (for external test vectors)
    if [ -f ".gitmodules" ]; then
        echo "📥 Initializing test vector submodules..."
        git submodule update --init --recursive
        echo "✅ Test vector submodules initialized"
    fi
    
    # Install test suites dependencies if it has its own pyproject.toml
    if [ -f "pyproject.toml" ]; then
        echo "📦 Installing test suites dependencies..."
        # Configure poetry to use the parent venv
        poetry config virtualenvs.create false
        poetry config virtualenvs.in-project false
        # Install just the dependencies from pyproject.toml
        poetry lock
        poetry install --only main --no-root || echo "   ⚠️ Warning: test-suites dependencies install failed"
        echo "✅ Test suites dependencies installed"
    fi
    
    cd ..
    echo "✅ Test suites setup complete"
else
    echo "ℹ️  Test suites not found (optional)"
fi

# Setup pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
poetry run pre-commit install
echo "✅ Pre-commit hooks installed"

# Initialize database directory
echo "💾 Initializing data directories..."
mkdir -p data/
echo "✅ Data directories created"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Run tests: poetry run poe test vectors --module safrole --spec tiny"
echo "   3. Start development: poetry run jam --env envs/40000.env"
echo ""