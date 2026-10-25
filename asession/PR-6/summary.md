# PR-6: Index factory-function operators and add workflows

https://github.com/PyLops/pylops-mcp/pull/6 (branch `factory-operators`)

## Summary
Completes the Phase 2 item "index operators built through factory functions".

- `pylops_mcp/introspect.py`: besides `LinearOperator` subclasses, plain functions in the `__all__` of `pylops.basicoperators`, `signalprocessing`, `waveeqprocessing` and `avo` and `medical` are indexed as operators (e.g. `FFT`, `FFT2D`, `Radon2D`, `MDC`, `PhaseShift`, avo modelling). Index grows from 71 to 88 operators.
- Functions that run an inversion or decomposition (`MDD`, `SeismicInterpolation`, `WavefieldDecomposition`, `Deghosting`, `PoststackInversion`, `PrestackInversion`, plus the plain classes `Marchenko` and `LSM`) are listed in an explicit `WORKFLOWS` set and get kind `workflow`.
- `pylops_mcp/server.py`: new tools `list_workflows(module?)` and `get_workflow(name)`; `search` accepts `kind="workflow"`.
- Catalog gains a `workflows` key; `index.json` regenerated; README tool table and `InitialPlan.md` updated.
- Tests: completeness test comparing the index against every public class and function in the `__all__` of those packages, plus tests for factory operators and the workflow tools.

## Decisions
- User asked for all public factory functions to be indexed; non-operator ones got their own kind rather than being dropped or mislabelled as operators.
- No backward-compat guard for old `index.json` files (dev phase): `load_index()` is unchanged.
- There is no `Index` operator in PyLops 2.8.0 (closest is the class `Restriction`, already indexed).

## Known limitations
- `WORKFLOWS` is hand-maintained: a new PyLops helper that runs an inversion would be indexed as an operator until added. The completeness test only guards against missing names, not misclassification.
- Public API is defined by package `__all__`, so public functions outside it (e.g. `avo.avo` scattering utilities) stay unindexed by design.

## Testing
- `make all` equivalent: pytest (14 passed), ruff, mypy all green.
- `python -m pylops_mcp.index`: 88 operators, 13 solvers, 8 workflows.
