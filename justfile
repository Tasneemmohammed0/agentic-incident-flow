# Run `just` to see all available recipes.

set dotenv-load := true

# Default recipe
default:
    @just --list

# Start the FastAPI development server
run:
    uv run uvicorn app.main:app --reload

# Start on a custom port
run-port PORT="8000":
    uv run uvicorn app.main:app --reload --port {{PORT}}

# Install dependencies
install:
    uv sync

# Add a new dependency
add PACKAGE:
    uv add {{PACKAGE}}

# Format code 
format:
    uv run ruff format .

# Lint code
lint:
    uv run ruff check .

# Run tests
test:
    uv run pytest

# Run lint + tests
check: lint test

# Remove Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete