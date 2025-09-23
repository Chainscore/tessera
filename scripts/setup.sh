#!/bin/bash
# scripts/setup-uv.sh - New streamlined setup script using uv

set -e

echo "🚀 Setting up Tessera development environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Verify Python version
echo "🐍 Checking Python version..."
if ! uv python find 3.12 &> /dev/null; then
    echo "📥 Installing Python 3.12..."
    uv python install 3.12
fi

# Initialize the workspace and install all dependencies
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
uv sync --all-extras

# Setup pre-commit hooks
echo "🔗 Setting up pre-commit hooks..."
uv run pre-commit install

# Initialize database directory
echo "💾 Initializing data directories..."
mkdir -p data/

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "   1. Run tests: uv run pytest"
echo "   2. Start development: uv run jam --env envs/40000.env" 
echo "   3. Add dependencies: uv add package-name"
echo "   4. Update dependencies: uv lock --upgrade"
echo ""
echo "💡 Key uv commands:"
echo "   - uv sync: Install/update all dependencies"
echo "   - uv run <command>: Run command in project environment"
echo "   - uv add <package>: Add new dependency"
echo "   - uv remove <package>: Remove dependency"
echo ""
