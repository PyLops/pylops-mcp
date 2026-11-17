# Development
.PHONY: sync test lint typecheck all

sync:
	uv sync --extra mpi

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

# Package to index: pylops, pyproximal or pylops_mpi (e.g. make index-missing PACKAGE=pyproximal)
PACKAGE ?= pylops

# Extra requirements of the isolated builds. pylops_mpi needs an MPI runtime,
# taken from the mpich wheel (on macOS, mpi4py may not find it: point
# MPI4PY_LIBMPI to the libmpi.*.dylib of the uv cache)
EXTRA_pylops_mpi = --with mpi4py --with mpich

# Release-specific pins as <version>:<requirement>. pylops-mpi 0.6.x imports
# names that PyLops removed after 2.6.0, and 0.7.0 imports a PyProximal helper
# that moved in 0.13.0
PINS_pylops_mpi = 0.6.0:pylops==2.6.0 0.6.1:pylops==2.6.0 0.7.0:pyproximal==0.12.0

# Index of the package installed in the project environment
index:
	uv run python -m pylops_mcp.index --package $(PACKAGE)

# Index of specific releases, each built in an isolated environment:
#   make index-all VERSIONS="2.4.0 2.5.0"
#   make index-all PACKAGE=pyproximal VERSIONS="0.9.0 0.10.0"
#   make index-all PACKAGE=pylops_mpi VERSIONS="0.5.0 0.6.0"
# (typing_extensions is added because pyproximal 0.11.0 imports it without declaring it)
index-all:
	@for v in $(VERSIONS); do \
		echo "== $(PACKAGE) $$v"; \
		pins=""; \
		for p in $(PINS_$(PACKAGE)); do \
			case $$p in $$v:*) pins="$$pins --with $${p#*:}";; esac; \
		done; \
		PYTHONPATH=. uv run --isolated --no-project --with "$(subst _,-,$(PACKAGE))==$$v" $(EXTRA_$(PACKAGE)) $$pins \
			--with numpydoc --with packaging --with typing_extensions python -m pylops_mcp.index \
			--package $(PACKAGE) \
			--out pylops_mcp/data/indexes/$(PACKAGE)/$$v.json || exit 1; \
	done

# Indexes for all PyPI releases (>= the minimum) that do not have one yet
index-missing:
	$(MAKE) index-all PACKAGE=$(PACKAGE) VERSIONS="$$(uv run python -m pylops_mcp.index --package $(PACKAGE) --missing | tr "\n" " ")"
