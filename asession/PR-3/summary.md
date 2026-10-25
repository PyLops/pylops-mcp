# PR-3: Prepare PyPI release

https://github.com/PyLops/pylops-mcp/pull/3 (branch `pypi-release`)

## Summary
Makes `claude mcp add --scope user pylops -- uvx pylops-mcp` possible (Phase 4, first point).

- `pyproject.toml`: license `LGPL-3.0-only`, authors, keywords, classifiers, project URLs; `local_scheme = "no-local-version"` (PyPI rejects local versions); slimmer sdist.
- `LICENSE`: replaced with LGPL-3.0 text.
- `.github/workflows/ci.yml`: `make all` on Python 3.10-3.13.
- `.github/workflows/release.yml`: `v*` tag -> build (fresh index) -> PyPI via Trusted Publishing; manual dispatch -> TestPyPI or PyPI.
- `README.md`: live install instructions, Claude Desktop snippet, PyPI badge, Releasing section.

## Known limitations
- Needs one-time setup: pending trusted publishers on PyPI/TestPyPI (workflow `release.yml`, environments `pypi`/`testpypi`) and matching GitHub environments.
- No automatic release on new PyLops versions yet.

## Testing
- `make all` green; `twine check` passes.
- Wheel smoke test via `uvx --from <wheel> pylops-mcp` over stdio: `search("convolution")` returns `Convolve1D`.
