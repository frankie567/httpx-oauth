# https://just.systems

install:
    uv sync --all-extras

lint:
    uv run ruff format .
    uv run ruff check --fix .
    uv run mypy httpx_oauth/

lint-check:
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy httpx_oauth/

test:
    uv run pytest

test-cov-xml:
    uv run pytest --cov-report=xml

docs-serve:
    uv run mkdocs serve

docs-build:
    uv run mkdocs build

version bump:
    uvx hatch version {{bump}}
