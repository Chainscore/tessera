#!/bin/bash
# scripts/setup.sh

# Ensure script fails on any error
set -e

# Check Python version
REQUIRED_PYTHON_VERSION="3.11"
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')

if [ $(echo "$PYTHON_VERSION < $REQUIRED_PYTHON_VERSION" | bc -l) -eq 1 ]; then
    echo "Error: Python $REQUIRED_PYTHON_VERSION or higher is required"
    exit 1
fi

# Install poetry if not present
if ! command -v poetry &> /dev/null; then
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
poetry install

# Setup pre-commit hooks
poetry run pre-commit install

# Initialize database directory
mkdir -p data/db

echo "Setup completed successfully!"