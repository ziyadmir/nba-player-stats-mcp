.PHONY: install test test-cov lint format clean run help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install package and dependencies"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage"
	@echo "  make lint       - Run linting checks"
	@echo "  make format     - Format code"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make run        - Run the MCP server"

install:
	pip install -e ".[dev]"

test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term

lint:
	# Check if ruff is installed, otherwise use pylint
	@which ruff > /dev/null 2>&1 && ruff check src/ tests/ || echo "Ruff not installed, skipping..."
	# Check Python files for basic issues
	python -m py_compile src/*.py tests/*.py

format:
	# Check if black is installed, otherwise skip
	@which black > /dev/null 2>&1 && black src/ tests/ || echo "Black not installed, skipping..."
	# Check if ruff is installed for import sorting
	@which ruff > /dev/null 2>&1 && ruff check --fix src/ tests/ || echo "Ruff not installed, skipping..."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info

run:
	python src/server.py

# Development install
dev-install:
	pip install -e ".[dev]"
	@echo "Installing additional dev tools..."
	pip install black ruff mypy