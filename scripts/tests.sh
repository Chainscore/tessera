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
    echo "Options:"
    echo "  -v, --verbose     Verbose test output"
    echo "  -k PATTERN        Run tests matching pattern"
    echo "  unit              Run unit tests"
    echo "  vectors           Run test vector validation"
    echo "  traces            Run test traces validation"
    echo "  all               Run all modules (vectors + traces) in order"
    echo "  -h, --help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 unit                # Run unit tests"
    echo "  $0 vectors --module X  # Run vectors for module X"
    echo "  $0 all                 # Run all modules in order"
}

# Parse arguments
TEST_PATTERN=""
UNIT=false
RUN_ALL=false
MODULE=""
SPEC=""
PATTERN="'*.json'"

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
        unit)
            print_info "Running unit tests..."
            PYTEST_ARGS="tests/unit"
            UNIT=true
            shift
            ;;
        vectors)
            PYTEST_ARGS="test-suites/harness/w3f/stf"
            shift
            ;;
        traces-linear)
            PYTEST_ARGS="test-suites/harness/w3f/traces/test_traces_linear.py"
            shift
            ;;
        traces)
            PYTEST_ARGS="test-suites/harness/w3f/traces/test_traces.py"
            shift
            ;;
        all)
            print_info "Running all modules (vectors + traces)..."
            RUN_ALL=true
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
        --pattern)
            PATTERN="$2"
            shift 2
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

# Run all modules (vectors + traces)
if [ "$RUN_ALL" = true ]; then
    VECTOR_MODULES="accumulate assurances authorizations disputes history preimages reports safrole statistics"
    TRACE_MODULES="fallback preimages preimages_light safrole storage storage_light"

    for module in $VECTOR_MODULES; do
        print_info "Running vectors for module: $module"
        poetry run pytest test-suites/harness/w3f/stf --module "$module" --pattern "$PATTERN" -vv -s || exit 1
    done

    for module in $TRACE_MODULES; do
        print_info "Running traces for module: $module"
        poetry run pytest test-suites/harness/w3f/traces --module "$module" --pattern "$PATTERN" -vv -s || exit 1
    done

    print_success "All modules (vectors + traces) finished successfully!"
    exit 0
fi

# Handle vectors with module and spec
if [ -n "$MODULE" ]; then
    print_info "Module: $MODULE"
    PYTEST_ARGS="$PYTEST_ARGS --module $MODULE"
fi
if [ -n "$SPEC" ]; then
    print_info "Spec: $SPEC"
    PYTEST_ARGS="$PYTEST_ARGS --spec $SPEC"
fi
if [ -n "$PATTERN" ]; then
    print_info "Pattern:\t$PATTERN"
    PYTEST_ARGS="$PYTEST_ARGS --pattern $PATTERN"
fi

# Add verbose
PYTEST_ARGS="$PYTEST_ARGS -vv -s"

if [ -n "$TEST_PATTERN" ]; then
    PYTEST_ARGS="$PYTEST_ARGS -k '$TEST_PATTERN'"
fi

# Run the tests normally
echo "Running tests with command: poetry run pytest $PYTEST_ARGS"
poetry run pytest $PYTEST_ARGS

if [ $? -eq 0 ]; then
    print_success "All tests passed!"
else
    print_error "Some tests failed"
    exit 1
fi
