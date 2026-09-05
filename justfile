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

# Run tests
test:
    python -m scripts.test_incidents \
    --kb data/kb_articles.json \
    --tests data/test_incidents.json \
    --verbose


# Remove Python cache files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete