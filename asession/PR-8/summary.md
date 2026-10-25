# PR-8: One index per PyLops version

Completes the Phase 2 item "one `index.json` per PyLops version".

## Summary
- `pylops_mcp/data/index.json` replaced by `pylops_mcp/data/indexes/<version>.json` for PyLops 2.4.0, 2.5.0, 2.6.0, 2.7.0 and 2.8.0 (1.5 MB in total, plain JSON).
- `pylops_mcp/index.py`: `write_index` writes to the version-named file; new `available_versions`, `resolve_version` (exact, then prefix such as "2.8" -> highest 2.8.x), `missing_versions` (queries PyPI); CLI gains `--out` and `--missing`. `load_index(version=None)` returns the latest; live introspection stays as the fallback when no files exist.
- `pylops_mcp/server.py`: all `search`/`list_*`/`get_*` tools take an optional `pylops_version`; catalogs load lazily and are cached per version; an unknown version returns `error` + `available_versions`. New `list_versions` tool, new resource `pylops://{pylops_version}/operators/{name}`; resources now return JSON instead of a dict repr.
- `introspect.py`: tolerate a missing public package (e.g. `pylops.medical` in older releases).
- Makefile: `index-all VERSIONS=...` (isolated `uv run --with pylops==X`, the package itself is not installed) and `index-missing`. `release.yml` runs `index-missing`.
- Tests for ordering (2.10 > 2.9), prefix resolution, default = latest, explicit older version, unknown version, and filename/`pylops_version` consistency.

## Decisions
- Minimum version 2.4.0; default is the latest shipped index, not the installed PyLops; plain JSON kept (wheel is compressed anyway).

## Known limitations
- `index-missing` in the release workflow builds missing indexes into the wheel but does not commit them; run it locally and commit to keep them in the repo.
- Operator counts: 81 (2.4/2.5), 84 (2.6), 87 (2.7), 88 (2.8). `WORKFLOWS` and `PUBLIC_PACKAGES` are not checked per version beyond import tolerance.

## Testing
- `make all`: pytest (20 passed), ruff, mypy green.
