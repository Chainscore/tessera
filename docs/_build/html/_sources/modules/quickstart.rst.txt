Quickstart
==========

This guide will help you get started with Tessera development.

Development Setup
--------------

1. Install Dependencies::

    # Ensure you have completed the installation guide first
    poetry install
    poetry shell

2. Verify Installation::

    # Run tests to verify everything is working
    pytest

Basic Usage
---------

1. Run the Node::

    # Start a development node
    jam

2. Run with Custom Config::

    # Use a specific chain spec
    jam --chain-spec=local

3. Connect to Network::

    # Connect to testnet
    jam --network=testnet

Development Workflow
-----------------

1. Make Changes::

    # Create a new branch
    git checkout -b feature/my-feature

    # Make your changes
    code .

2. Test Changes::

    # Run unit tests
    pytest tests/unit

    # Run specific test
    pytest tests/unit/test_file.py::test_function

    # Run with coverage
    pytest --cov=jam

3. Format and Lint::

    # Format code
    black .
    isort .

    # Run linter
    flake8

4. Commit Changes::

    # Stage changes
    git add .

    # Commit (this will trigger pre-commit hooks)
    git commit -m "feat: add new feature"

Testing Guide
-----------

Project Structure::

    tests/
    ├── fixtures/       # Shared test fixtures
    ├── integration/    # Integration tests
    └── unit/          # Unit tests

Running Tests::

    # Run all tests
    pytest

    # Run with output
    pytest -v

    # Run specific directory
    pytest tests/unit/

    # Run with coverage
    pytest --cov=jam --cov-report=html

Writing Tests::

    # Example test file
    def test_feature():
        # Arrange
        input_data = ...

        # Act
        result = process(input_data)

        # Assert
        assert result == expected

Using Fixtures::

    # In conftest.py
    @pytest.fixture
    def test_data():
        return ...

    # In test file
    def test_with_fixture(test_data):
        assert process(test_data) == expected

Next Steps
---------

1. Review the :doc:`architecture` documentation
2. Explore the Core Concepts section
3. Check out example implementations
4. Join the developer community 