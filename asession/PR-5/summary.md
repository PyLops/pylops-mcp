# PR-5: Migrate to `mcp` 2.x

https://github.com/PyLops/pylops-mcp/pull/5 (branch `mcp-v2`)

## Summary
First Phase 2 item: drop the `mcp<2` pin and move from `FastMCP` to `MCPServer`.

- `pyproject.toml`: `mcp[cli]>=2,<3`; `uv.lock` updated (mcp 1.30.0 -> 2.3.0).
- `pylops_mcp/server.py`: `from mcp.server.mcpserver import MCPServer`, `MCPServer("pylops")`. Decorators and `mcp.run()` are unchanged in v2.
- `asession/InitialPlan.md`: item marked done; Phase 3 transport line updated (`json_response`/`stateless_http` now go to `run()`).

## Known limitations
- Anyone installing alongside other packages that require `mcp<2` can no longer share an environment.

## Testing
- `make all` green (8 tests, ruff, mypy).
- Stdio smoke test with an `mcp` client: 5 tools listed, `get_operator("Convolve1D")` works, `pylops://operators/{name}` resource reads (including the unknown-name suggestions path).
