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

# Package to index: pylops or pyproximal (e.g. make index-missing PACKAGE=pyproximal)
PACKAGE ?= pylops

# Index of the package installed in the project environment
index:
	uv run python -m pylops_mcp.index --package $(PACKAGE)

# Index of specific releases, each built in an isolated environment:
#   make index-all VERSIONS="2.4.0 2.5.0"
#   make index-all PACKAGE=pyproximal VERSIONS="0.9.0 0.10.0"
# (typing_extensions is added because pyproximal 0.11.0 imports it without declaring it)
index-all:
	@for v in $(VERSIONS); do \
		echo "== $(PACKAGE) $$v"; \
		PYTHONPATH=. uv run --isolated --no-project --with "$(PACKAGE)==$$v" \
			--with numpydoc --with packaging --with typing_extensions python -m pylops_mcp.index \
			--package $(PACKAGE) \
			--out pylops_mcp/data/indexes/$(PACKAGE)/$$v.json || exit 1; \
	done

# Indexes for all PyPI releases (>= the minimum) that do not have one yet
index-missing:
	$(MAKE) index-all PACKAGE=$(PACKAGE) VERSIONS="$$(uv run python -m pylops_mcp.index --package $(PACKAGE) --missing | tr "\n" " ")"
