Testing Guide
============

This guide covers testing practices and methodologies used in Tessera development.

Test Structure
------------

The test suite is organized into three main categories::

    tests/
    ├── fixtures/       # Shared test fixtures and utilities
    ├── integration/    # End-to-end and integration tests
    └── unit/          # Unit tests for individual components

Testing Tools
-----------

Tessera uses these testing tools:

* **pytest**: Main testing framework
* **pytest-cov**: Code coverage reporting
* **pytest-asyncio**: Async test support
* **hypothesis**: Property-based testing

Running Tests
-----------

Basic Usage::

    # Run all tests
    pytest

    # Run with verbose output
    pytest -v

    # Run specific test file
    pytest tests/unit/test_state.py

    # Run specific test function
    pytest tests/unit/test_state.py::test_state_transition

Coverage Reports::

    # Generate coverage report
    pytest --cov=jam

    # Generate HTML report
    pytest --cov=jam --cov-report=html

    # View report in browser
    open htmlcov/index.html

Writing Tests
-----------

1. Unit Tests::

    # tests/unit/test_feature.py
    import pytest
    from jam.feature import Feature

    def test_feature_behavior():
        # Arrange
        feature = Feature()
        
        # Act
        result = feature.process()
        
        # Assert
        assert result == expected

2. Integration Tests::

    # tests/integration/test_workflow.py
    import pytest
    from jam.workflow import Workflow

    @pytest.mark.asyncio
    async def test_end_to_end():
        # Setup
        workflow = Workflow()
        
        # Execute
        result = await workflow.run()
        
        # Verify
        assert result.status == "success"

Using Fixtures
-----------

1. Create Fixtures::

    # tests/fixtures/conftest.py
    import pytest
    
    @pytest.fixture
    def test_data():
        return {
            "key": "value"
        }
    
    @pytest.fixture
    async def async_resource():
        resource = await setup_resource()
        yield resource
        await cleanup_resource()

2. Use Fixtures::

    # tests/unit/test_feature.py
    def test_with_fixture(test_data):
        assert process(test_data) == expected

    @pytest.mark.asyncio
    async def test_async(async_resource):
        result = await async_resource.query()
        assert result

Property-Based Testing
-------------------

Using Hypothesis::

    from hypothesis import given, strategies as st

    @given(st.integers(), st.integers())
    def test_addition_properties(x, y):
        result = add(x, y)
        assert result == add(y, x)  # Commutative
        assert add(result, 0) == result  # Identity

Mocking
------

Using pytest-mock::

    def test_with_mock(mocker):
        # Create mock
        mock_db = mocker.patch('jam.database.Database')
        mock_db.query.return_value = expected_result
        
        # Use mock
        result = process_data()
        
        # Verify
        mock_db.query.assert_called_once()
        assert result == expected_result

Best Practices
------------

1. Test Organization:
   * One test file per module
   * Clear test names describing behavior
   * Group related tests in classes

2. Test Design:
   * Follow Arrange-Act-Assert pattern
   * Test edge cases and error conditions
   * Keep tests focused and isolated

3. Fixtures:
   * Use fixtures for common setup
   * Clean up resources properly
   * Share fixtures via conftest.py

4. Coverage:
   * Aim for high test coverage
   * Focus on critical paths
   * Don't sacrifice quality for coverage

5. Performance:
   * Keep tests fast
   * Use async testing where appropriate
   * Minimize external dependencies 