# PR-10: Add PyProximal tools with per-version indexes

- URL: https://github.com/PyLops/pylops-mcp/pull/10
- Branch: `pyproximal-tools`

## Summary
- New tools `list_proxperators`, `list_proxsolvers`, `get_proxoperator`, `get_proxsolver`, each with an optional `pyproximal_version` (prefix resolution, `error` + `available_versions` on unknown version, close-match `suggestions` on unknown name).
- New resources `pyproximal://operators/{name}` and `pyproximal://{pyproximal_version}/operators/{name}`.
- One index per PyProximal release >= 0.9.0 (0.9.0, 0.10.0, 0.11.0, 0.11.1, 0.12.0, 0.13.0) in `pylops_mcp/data/indexes/pyproximal/`; PyLops indexes moved (`git mv`) to `indexes/pylops/` for symmetry.

## What changed
- `introspect.py`: `build_catalog` renamed `build_pylops_catalog`; new `build_pyproximal_catalog`. Operators = `pyproximal.proximal.__all__` (includes the `Simplex` factory function). Solvers = public functions defined in `pyproximal.optimization.*` (the PyLops lowercase-name rule can't be reused: PyProximal solvers are capitalized).
- `index.py`: `Package` dataclass and `PACKAGES` registry; `write_index`, `available_versions`, `resolve_version`, `load_index`, `missing_versions` take a `package` argument; CLI gains `--package`. Min versions: pylops 2.4.0, pyproximal 0.9.0.
- `server.py`: `_catalog`/`_lookup`/`_list`/`_unknown_version` parameterized by package; responses carry `pylops_version` or `pyproximal_version` accordingly.
- Makefile: `PACKAGE` variable (default pylops) on `index`, `index-all`, `index-missing`; isolated builds add `typing_extensions` (pyproximal 0.11.0 imports it without declaring it).
- CI: Update indexes workflow has a `package` input; release workflow checks missing indexes for both packages.
- `pyproject.toml`: `pyproximal>=0.9.0` dependency, mypy override; `uv.lock` updated.
- README: new tool rows, resources, rebuild instructions.

## Breaking changes
- `list_versions()` returns `{"pylops": {default, versions}, "pyproximal": {default, versions}}`.
- `search` takes `pyproximal_version` and kinds `proxoperator`/`proxsolver`; `kind="all"` spans both packages.

## Notes / limitations
- `RED` exists both as a proximal operator and as a solver; they live in separate pools.
- Older PyProximal indexes have fewer entries (0.9.0: 34 operators, 17 solvers; 0.13.0: 40 operators, 22 solvers).

## Testing
`make all`: 31 tests, ruff and mypy pass; all 12 tools register on the server.
