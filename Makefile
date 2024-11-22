# Makefile
.PHONY: setup test lint format clean

setup:
	./scripts/setup.sh

test:
	pytest tests/

lint:
	flake8 jam tests
	mypy jam tests
	black --check jam tests
	isort --check-only jam tests

format:
	black jam tests
	isort jam tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete