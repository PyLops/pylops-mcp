# Development
.PHONY: sync test lint typecheck all

sync:
	uv sync

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy pylops_mcp

all: test lint typecheck


# Index creation
.PHONY: index

index:
	uv run python -m pylops_mcp.index
