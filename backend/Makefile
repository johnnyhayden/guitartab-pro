.PHONY: install fmt lint test clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  fmt        - Format code with black and isort"
	@echo "  lint       - Run flake8 linting"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up temporary files"
	@echo "  shell      - Activate pipenv shell"

# Install dependencies
install:
	pipenv install --dev

# Format code
fmt:
	pipenv run black .
	pipenv run isort .

# Run linting
lint:
	pipenv run flake8

# Run tests
test:
	pipenv run python -m pytest

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Activate pipenv shell
shell:
	pipenv shell
