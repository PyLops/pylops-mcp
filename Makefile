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
.PHONY: index index-all index-missing

# Index of the PyLops installed in the project environment
index:
	uv run python -m pylops_mcp.index

# Index of specific PyLops releases, each built in an isolated environment:
#   make index-all VERSIONS="2.4.0 2.5.0"
index-all:
	@for v in $(VERSIONS); do \
		echo "== PyLops $$v"; \
		PYTHONPATH=. uv run --isolated --no-project --with "pylops==$$v" \
			--with numpydoc --with packaging python -m pylops_mcp.index \
			--out pylops_mcp/data/indexes/$$v.json || exit 1; \
	done

# Indexes for all PyPI releases (>= 2.4.0) that do not have one yet
index-missing:
	$(MAKE) index-all VERSIONS="$$(uv run python -m pylops_mcp.index --missing | tr "\n" " ")"
