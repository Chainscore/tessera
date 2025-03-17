# 🧪 Testing Guidelines for Tessera

This document outlines our testing standards and best practices for ensuring quality in the Tessera project.

## 🎯 Testing Philosophy

We follow these core testing principles:

1. **Early & Often**: Test as you code, not after
2. **Comprehensive Coverage**: Aim for >80% code coverage
3. **Test Pyramid**: More unit tests, fewer integration/E2E tests
4. **Deterministic**: Tests should have consistent results
5. **Independent**: Tests should not depend on each other

## 📦 Testing Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── consensus/     # Tests for consensus module
│   ├── network/       # Tests for network module
│   └── ...
├── integration/       # Integration tests (component interaction)
├── functional/        # Functional tests (behavior-focused)
├── e2e/               # End-to-end tests
├── fixtures/          # Shared test fixtures
└── conftest.py        # Global pytest configuration
```

## 🛠️ Testing Tools

- **pytest**: Main testing framework
- **pytest-cov**: Code coverage measurement
- **pytest-asyncio**: Testing async code
- **pytest-xdist**: Parallel test execution
- **hypothesis**: Property-based testing
- **tox**: Testing against multiple environments

## 📋 Types of Tests

### 🔬 Unit Tests

Test individual functions, classes, or modules in isolation:

```python
def test_block_validation():
    """Test that valid blocks pass validation."""
    # Arrange
    block = Block(hash="0x123", prev_hash="0x456", data="test")
    
    # Act
    result = validate_block(block)
    
    # Assert
    assert result is True
```

### 🧩 Integration Tests

Test how components work together:

```python
def test_consensus_with_state():
    """Test consensus module interacts correctly with state."""
    # Arrange
    consensus = Consensus()
    state = State()
    
    # Act
    consensus.process_block(block, state)
    
    # Assert
    assert state.head == block.hash
```

### 🔄 Functional Tests

Test behavior of the system from a user perspective:

```python
def test_cli_creates_block():
    """Test that CLI command creates a block."""
    # Arrange
    runner = CliRunner()
    
    # Act
    result = runner.invoke(cli, ["create-block", "--data", "test"])
    
    # Assert
    assert "Block created" in result.output
    assert result.exit_code == 0
```

### 🌐 End-to-End Tests

Test complete workflows through the entire system:

```python
def test_node_syncs_with_network():
    """Test that a node can sync with the network."""
    # Arrange (start multiple nodes in containers)
    network = TestNetwork(nodes=3)
    
    # Act
    network.start()
    network.wait_for_sync(timeout=30)
    
    # Assert
    assert network.nodes[0].head == network.nodes[1].head
```

## 🧰 Testing Techniques

### 📊 Test Coverage

We aim for high code coverage:

```bash
# Run tests with coverage
pytest --cov=jam --cov-report=html

# Coverage targets:
# - Unit tests: 90%+
# - Overall: 80%+
```

### 🎲 Property-Based Testing

Use [Hypothesis](https://hypothesis.readthedocs.io/) for generating test cases:

```python
from hypothesis import given, strategies as st

@given(st.binary(min_size=32, max_size=32))
def test_block_with_random_hash(random_hash):
    """Test block creation with random hash values."""
    block = Block(hash=random_hash)
    assert block.validate_hash()
```

### 🤡 Mocking

Use `unittest.mock` or `pytest-mock` for isolation:

```python
def test_network_discovery(mocker):
    """Test peer discovery without real network calls."""
    # Arrange
    mock_response = mocker.patch("jam.network.discovery.request", return_value=["peer1", "peer2"])
    
    # Act
    peers = discover_peers()
    
    # Assert
    assert len(peers) == 2
    mock_response.assert_called_once()
```

### 🔄 Parametrized Tests

Test multiple scenarios with single function:

```python
@pytest.mark.parametrize("block_size,is_valid", [
    (1024, True),      # Valid block size
    (0, False),        # Too small
    (2*1024*1024, False)  # Too large
])
def test_block_size_validation(block_size, is_valid):
    """Test block size validation with different sizes."""
    block = Block(data="x" * block_size)
    assert block.is_valid_size() == is_valid
```

### ⚡ Performance Testing

Test for performance regressions:

```python
def test_block_processing_performance(benchmark):
    """Test block processing performance."""
    def setup():
        return generate_test_block()
        
    def process(block):
        return process_block(block)
    
    # This will run process() multiple times and assert it's within expected range
    result = benchmark.pedantic(process, setup=setup, iterations=100, rounds=10)
    
    assert result  # Check result is valid
    # Benchmark will automatically fail if performance degrades significantly
```

## 🔄 Testing Workflow

### 🚀 Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_consensus.py

# Run specific test function
pytest tests/unit/test_consensus.py::test_block_validation

# Run tests by marker
pytest -m "slow"

# Run with output
pytest -v

# Run with parallelization
pytest -xvs
```

### 🏷️ Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_large_chain_validation():
    """Test that might take longer to run."""
    # ...

@pytest.mark.network
def test_peer_discovery():
    """Test requiring network access."""
    # ...
```

Configure in `pytest.ini`:
```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    network: marks tests that require network access
```

## 📐 Testing Standards

### ✨ Test Naming

- Format: `test_[function]_[scenario]_[expected]`
- Examples: 
  - `test_block_validation_with_invalid_hash_fails`
  - `test_peer_discovery_with_empty_network_returns_empty_list`

### 🏗️ Test Structure

Follow the Arrange-Act-Assert (AAA) pattern:

```python
def test_example():
    # Arrange - set up test data
    input_data = "test"
    
    # Act - execute the code being tested
    result = process(input_data)
    
    # Assert - verify the result
    assert result == expected
```

### 📝 Test Documentation

Each test should have:
- Clear docstring explaining purpose
- Comments for complex test steps
- Explicit assertions with messages

```python
def test_state_transition():
    """Test that state transitions correctly when given valid input.
    
    This verifies the core state machine logic.
    """
    # ...
    assert new_state.head == block.hash, "Head should update to new block"
```

## 📚 Fixtures and Helpers

### 🧩 Test Fixtures

Create reusable fixtures in `conftest.py`:

```python
@pytest.fixture
def genesis_block():
    """Create a genesis block for testing."""
    return Block(
        hash="0x000000",
        prev_hash=None,
        timestamp=0,
        data="genesis"
    )

@pytest.fixture
def blockchain(genesis_block):
    """Create a test blockchain with genesis block."""
    chain = Blockchain()
    chain.add_block(genesis_block)
    return chain
```

### 🛠️ Test Helpers

Create helper functions for common testing tasks:

```python
def create_chain_with_blocks(num_blocks):
    """Helper to create a blockchain with specified number of blocks."""
    chain = Blockchain()
    blocks = []
    
    # Add genesis block
    genesis = Block(hash="0x000000", prev_hash=None, data="genesis")
    chain.add_block(genesis)
    blocks.append(genesis)
    
    # Add additional blocks
    for i in range(1, num_blocks):
        block = Block(
            hash=f"0x{i:06x}",
            prev_hash=blocks[-1].hash,
            data=f"block {i}"
        )
        chain.add_block(block)
        blocks.append(block)
    
    return chain, blocks
```

## 🚀 Continuous Integration

Every PR should include:
- New tests for new features
- Updated tests for modified code
- All tests passing
- Coverage maintained or improved

CI pipeline will:
- Run all tests
- Verify code coverage
- Run slow/integration tests nightly

## 🔍 Testing Blockchain-Specific Components

### 🔗 Consensus Testing

- Test for fork choices
- Test for different network conditions
- Test for Byzantine scenarios (conflicting blocks)
- Test for recovery after partitioning

### 🌐 P2P Network Testing

- Test for peer discovery
- Test for message propagation
- Test for network partitioning recovery
- Test for bandwidth limitations

### 📊 State Testing

- Test for state transitions
- Test for invalid transitions
- Test for state rollbacks
- Test for large state operations

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Property-Based Testing with Hypothesis](https://hypothesis.readthedocs.io/)
- [Test Driven Development Guide](https://www.agilealliance.org/glossary/tdd/)
- [Martin Fowler on Test Pyramids](https://martinfowler.com/articles/practical-test-pyramid.html)
