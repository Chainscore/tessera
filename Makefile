# Makefile
.PHONY: setup test lint format clean

setup:
	uv sync
	uv run pre-commit install

test:
	uv run pytest tests/

lint:
	uv run flake8 jam tests
	uv run mypy jam tests
	uv run black --check jam tests
	uv run isort --check-only jam tests

format:
	uv run black jam tests
	uv run isort jam tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete