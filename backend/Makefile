.PHONY: install fmt lint test clean help db-init db-drop db-migrate db-upgrade db-downgrade

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  fmt        - Format code with black and isort"
	@echo "  lint       - Run flake8 linting"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up temporary files"
	@echo "  shell      - Activate pipenv shell"
	@echo "  db-init    - Initialize database tables"
	@echo "  db-drop    - Drop all database tables"
	@echo "  db-migrate - Create new migration"
	@echo "  db-upgrade - Upgrade database to latest migration"
	@echo "  db-downgrade - Downgrade database by one migration"

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

# Database commands
db-init:
	python scripts/migrate.py init

db-drop:
	python scripts/migrate.py drop

db-migrate:
	@read -p "Enter migration message: " msg; \
	python scripts/migrate.py create "$$msg"

db-upgrade:
	python scripts/migrate.py upgrade

db-downgrade:
	python scripts/migrate.py downgrade
