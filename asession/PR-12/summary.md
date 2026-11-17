# PR-12: Add PyLops-MPI tools with per-version indexes

- URL: https://github.com/PyLops/pylops-mcp/pull/12
- Branch: `pylops-mpi-tools`

## Summary
- New tools `list_mpioperators`, `list_mpisolvers`, `list_mpiproxoperators`, `list_mpiproxsolvers`, `list_mpiarrays` and the matching `get_mpi*` tools, each with an optional `pylops_mpi_version` (same version resolution, `error` + `available_versions` and `suggestions` behaviour as the PyLops/PyProximal tools). 22 tools in total.
- New resources `pylops-mpi://operators/{name}` and `pylops-mpi://{pylops_mpi_version}/operators/{name}`.
- One index per PyLops-MPI release >= 0.5.0 (0.5.0, 0.6.0, 0.6.1, 0.7.0, 0.8.0) in `pylops_mcp/data/indexes/pylops_mpi/`.

## What changed
- `introspect.py`: `build_pylops_mpi_catalog` with five pools: `operators` (subclasses of `MPILinearOperator`/`MPIStackedLinearOperator` plus factory functions from `MPI_PUBLIC_PACKAGES`' `__all__`, e.g. `MPIMDC`), `solvers` (lowercase functions in `pylops_mpi.optimization.*`, excluding `utils`), `proxoperators`, `proxsolvers` (empty before 0.7.0) and `arrays` (`DistributedArray`, `StackedDistributedArray`, `Partition`).
- `index.py`: `pylops_mpi` registered in `PACKAGES` (min version 0.5.0).
- `server.py`: `POOL_KEYS`/`SEARCH_KINDS` extended; `search` takes `pylops_mpi_version` and kinds `mpioperator`, `mpisolver`, `mpiproxoperator`, `mpiproxsolver`, `mpiarray`.
- `pyproject.toml`: optional extra `mpi = ["pylops-mpi>=0.5.0"]`; mypy overrides for `pylops_mpi`, `mpi4py`. Not a hard dependency: the server reads the shipped indexes.
- Makefile: `make sync` installs the extra; `index-all` adds `mpi4py` + `mpich` for `pylops_mpi` and supports per-release pins (`PINS_pylops_mpi`).
- CI: installs `libopenmpi-dev` and syncs the extra; index and release workflows know `pylops_mpi`.

## Notes / limitations
- Old releases need pins to import with current dependencies: 0.6.0/0.6.1 need `pylops==2.6.0` (they import `Tuple` from `pylops.utils.typing`), 0.7.0 needs `pyproximal==0.12.0` (`_x0z0_init` moved in 0.13.0).
- On macOS, mpi4py does not find the mpich wheel's library; building locally needs `MPI4PY_LIBMPI=<uv cache>/lib/libmpi.12.dylib`.
- Class-based solvers (`CG`, `CGLS`, `ISTA`, `FISTA`) are not indexed, as for PyLops.
- Tests that introspect live skip when `pylops_mpi` or MPI cannot be imported.

## Testing
`make all` (without MPI): 40 passed, 2 skipped; with MPI available: 42 passed; ruff and mypy pass.
