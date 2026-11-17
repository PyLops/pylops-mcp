# PR 11: Add PyLops 2.9.0 index

- URL: https://github.com/PyLops/pylops-mcp/pull/11
- Branch: pylops-2.9.0-index

## Why
PyLops 2.9.0 was on PyPI without an index, so the MCP tools still defaulted to 2.8.0 (and the release check would fail on a missing index).

## What
- `pylops_mcp/data/indexes/pylops/2.9.0.json`: 93 operators, 13 solvers, 8 workflows, built with `make index-all VERSIONS="2.9.0"`. New since 2.8.0: `Downsample2D`, `MultiOperator`, `SWT`, `SWT2D`, `SWTND`; nothing removed.
- `asession/InitialPlan.md`: roadmap items annotated with the PRs that delivered them (separate commit).

## Limitations / testing
- `make all` (31 tests, ruff, mypy) passes; `--missing` no longer lists 2.9.0.
- `pyproject.toml` still requires `pylops>=2.8.0` for the live environment; not changed.
