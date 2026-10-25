# PR-2: Add `list_solvers` tool

https://github.com/PyLops/pylops-mcp/pull/2 (branch `add-list-solver`)

## Summary
Adds a `list_solvers` MCP tool that mirrors `list_operators` for solvers.

- `pylops_mcp/server.py`: `list_solvers(module=None)` returns the sorted solver names (key `solvers`) plus `pylops_version`, optionally filtered by module substring (e.g. `"sparsity"`, `"leastsquares"`, `"basic"`, `"eigs"`).
- `README.md`: new row in the tools table.
- `tests/test_server.py`: `test_list_solvers_module_filter`.

## Known limitations
- Module filter is a substring match, same as `list_operators`.

## Testing
- `uv run pytest`: 8 tests pass.
