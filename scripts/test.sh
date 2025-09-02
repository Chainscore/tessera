#!/bin/bash

# Tessera Test Runner
# Intelligently runs tests based on platform capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Show help
show_help() {
    echo "Tessera Test Runner - Platform-aware test execution"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_CATEGORY|TEST_PATH]"
    echo ""
    echo "Test Categories:"
    echo "  pure       - Pure Python tests (always available)"
    echo "  db         - Database tests (requires RocksDB)"
    echo "  pvm        - PVM execution tests (Linux only)"
    echo "  compatible - All tests compatible with current platform (default)"
    echo "  all        - All tests (may fail on some platforms)"
    echo ""
    echo "Options:"
    echo "  -v, --verbose     Verbose test output"
    echo "  -k PATTERN        Run tests matching pattern"
    echo "  --unit            Run unit tests"
    echo "  --vectors         Run test vector validation"
    echo "  --traces          Run test traces validation"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                   # Run compatible tests"
    echo "  $0 pure              # Run only pure Python tests"
    echo "  $0 db                # Run database tests"
    echo "  $0 tests/unit/types  # Run specific test path"
    echo "  $0 --check           # Check what tests can run"
}

# Parse arguments
TEST_PATTERN=""
UNIT=false
VECTORS=false
TRACES=false
MODULE=""
SPEC=""

# Construct pytest command
PYTEST_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -k)
            TEST_PATTERN="$2"
            shift 2
            ;;
        --unit)
            print_info "Running unit tests..."
            PYTEST_ARGS="tests/unit"
            UNIT=true
            shift
            ;;
        --vectors)
            VECTORS=true
            shift
            ;;
        --module)
            MODULE="$2"
            shift 2
            ;;
        --spec)
            SPEC="$2"
            shift 2
            ;;
        --traces-linear)
            TRACES=true
            PYTEST_ARGS="test-suites/harness/w3f/traces/test_traces_linear.py"
            shift
            ;;
        *)
            # If it doesn't match any option, treat as test path
            if [ -z "$PYTEST_ARGS" ]; then
                PYTEST_ARGS="$1"
            fi
            shift
            ;;
    esac
done

# Handle vectors with module and spec
if [ "$VECTORS" = true ]; then
    PYTEST_ARGS="test-suites/harness/w3f/stf"
    if [ -n "$MODULE" ]; then
        PYTEST_ARGS="$PYTEST_ARGS --module $MODULE"
    fi
    if [ -n "$SPEC" ]; then
        PYTEST_ARGS="$PYTEST_ARGS --spec $SPEC"
    fi
    print_info "Running vector tests with module: $MODULE, spec: $SPEC"
fi

# Default to unit tests if no specific test path given
if [ -z "$PYTEST_ARGS" ]; then
    PYTEST_ARGS="tests/unit"
    print_info "No specific tests specified, running unit tests"
fi

# Add verbose
PYTEST_ARGS="$PYTEST_ARGS -vv -s"

# Ensure we're in the project root
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the tessera project root"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    print_info "Activated virtual environment"
else
    print_warning "No virtual environment found. Run scripts/setup.sh first."
fi

if [ -n "$TEST_PATTERN" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -k '$TEST_PATTERN'"
fi

# Run the tests
echo "Running tests with command: poetry run pytest $PYTEST_ARGS"
poetry run pytest $PYTEST_ARGS

if [ $? -eq 0 ]; then
    print_success "All tests passed!"
else
    print_error "Some tests failed"
    exit 1
fi
