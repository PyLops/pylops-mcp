# PR-1: Add core PyLops MCP server (phase 1)

https://github.com/PyLops/pylops-mcp/pull/1 (branch `phase1-core-server`)

## Summary
First deliverable of the roadmap in `asession/InitialPlan.md` (Phase 1 only): a local stdio MCP server that lets agents and users query PyLops operators and solvers in a structured way instead of web search / file crawling.

- `pylops_mcp/introspect.py`: walks the installed PyLops and uses numpydoc to describe operators (`LinearOperator` subclasses) and solvers (functions in `pylops.optimization.*`): signature, parameters, notes, examples.
- `pylops_mcp/index.py`: dumps the catalog to `pylops_mcp/data/index.json` (`make index`) and loads it at startup, falling back to live introspection.
- `pylops_mcp/server.py` (FastMCP): tools `search`, `list_operators`, `get_operator`, `get_solver`, plus resource `pylops://operators/{name}`. Responses include `pylops_version`; unknown names return close-match suggestions.
- `pylops-mcp` console script, so `claude mcp add pylops -- uv run pylops-mcp` works.
- uv/hatch-vcs scaffold with ruff, mypy, pytest and a Makefile (`make all`).
- `mcp` is pinned to `<2` (2.x renamed `FastMCP`); migrating is the first item of Phase 2.

Current index (PyLops 2.8.0): 71 operators, 13 solvers.

## Known limitations
- Operators built through factory functions (e.g. `FFT`, `Radon2D`) are not `LinearOperator` classes and are not indexed yet.
- Solver list includes helpers such as `power_iteration` and `normal_equations_inversion`.
- `recommend_solver` was dropped from scope for now.

## Testing
- `make all`: 7 tests pass, ruff and mypy clean.
- Not yet verified: running the server over stdio end to end (MCP Inspector / Claude Code).
