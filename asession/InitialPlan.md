# Plan: pylops-mcp — structured query server for PyLops operators and solvers

## Context
Agents and users currently find PyLops operators/solvers via web search and file crawling. The shared chat
(claude.ai/share/ba29a3b9-...) proposes an MCP server that introspects PyLops (numpydoc) and exposes narrow,
structured tools. It ships two ways from one codebase: a free local package (`uvx pylops-mcp`, stdio) and an
optional hosted Streamable-HTTP endpoint (no OAuth, read-only, rate-limited). Hosting cost is near zero (free tier
or ~$5/mo VPS); users' own Claude plans cover token usage.

Starting point: the uv/hatch scaffold already in `/Users/mrava87/Desktop/OpenSource/pylops-mcp`
(`pylops_mcp/`, `tests/`, `Makefile`, ruff + mypy strict-ish, `make all` green). `pylops_mcp/basic.py` is a
placeholder to be replaced.

## Phase 1 — Core server (MVP, local stdio)
1. `pyproject.toml`: add deps `mcp[cli]`, `pylops`, `numpydoc`; add `[project.scripts] pylops-mcp = "pylops_mcp.server:main"`; add `description` and README.
2. `pylops_mcp/introspect.py`: `build_catalog()` walks `pylops.*`, collects `LinearOperator` subclasses (excluding the base) and functions in `pylops.optimization.*`; `describe(obj)` uses `numpydoc` `ClassDoc`/`FunctionDoc` to return name, module, signature, summary, parameters, notes, examples. Skip modules that fail to import (optional deps). Include `pylops_version`.
3. `pylops_mcp/index.py`: dump the catalog to a versioned JSON (`pylops_mcp/data/index.json`), and load it at startup (fall back to live introspection if missing). Exclude from VCS if generated at release; include in wheel via hatch config.
4. `pylops_mcp/server.py` (FastMCP): tools `search(query, kind)`, `list_operators(module?)`, `get_operator(name)`, `get_solver(name)`; resource `pylops://operators/{name}`. Every response carries `pylops_version`. Clear error (not KeyError) for unknown names, with close-match suggestions.
5. Remove `basic.py` and `tests/test_basic.py`.

## Phase 2 — Quality improvements
- Migrate to `mcp` 2.x: drop the `mcp<2` pin, switch `FastMCP` (`mcp.server.fastmcp`) to `MCPServer` (`mcp.server.mcpserver`), and adapt other changed APIs (see https://py.sdk.modelcontextprotocol.io/v2/migration/).
- Index operators built through factory functions (e.g. `FFT`, `Radon2D`): they are functions returning `LinearOperator` objects, not `LinearOperator` subclasses, so Phase 1 introspection misses them.
- Index the PyLops `examples/` gallery by imported operators and return them from `get_operator`.
- Structured fields: `explicit`, dtype, shape semantics, CuPy/JAX backend support, for filtering.
- Better search: token/fuzzy scoring over name, summary, tags; embeddings only if substring search proves insufficient.
- `recommend_solver(problem)` (rule-based problem → solver map) — dropped for now, revisit later.
- Optional `run_snippet` sandbox (dottest) — deferred; needs a security review first.

## Phase 3 — Remote hosting
- `FastMCP("pylops", stateless_http=True, json_response=True)`; `mcp.run(transport="streamable-http")` via a `--http` CLI flag.
- Dockerfile with the prebuilt index (no heavy PyLops import per request); deploy to Cloud Run/Fly.io/Cloudflare behind HTTPS with rate limiting. No OAuth (public read-only data).

## Phase 4 — Release and discovery
- GitHub Actions: on new PyLops release, rebuild the index, run tests, publish to PyPI (`uvx pylops-mcp`).
  - Done (PR-3): CI + tag-triggered release workflow with Trusted Publishing, PyPI metadata, LGPL-3.0. Still open: automatic trigger on new PyLops releases.
- Publish `server.json` to the Official MCP Registry; consider submitting to the Claude Connectors Directory; optional Claude Code plugin (MCP + skill).
- README: install snippets for Claude Code (`claude mcp add pylops -- uvx pylops-mcp`, and `--transport http` for remote), Claude Desktop (config JSON/.mcpb), and claude.ai custom connector (paid plan; verify current rules).

## Critical files
- `pyproject.toml`, `pylops_mcp/{introspect,index,server}.py`, `tests/`, `Makefile` (add an `index` target: `uv run python -m pylops_mcp.index`).

## Verification
- `make all` (pytest, ruff, mypy) green.
- Tests: `get_operator("Convolve1D")` schema; `search("convolution")` returns Convolve1D; unknown name returns a helpful error; `pylops_version` present.
- Manual: `uv run mcp dev pylops_mcp/server.py` (Inspector); `claude mcp add pylops -- uv run pylops-mcp` then query from Claude Code.
- Phase 3: `curl` the `/mcp` endpoint locally; test in claude.ai (known reports of custom connector tools not surfacing — test each client before announcing).

## Decisions
- First delivery scope: **Phase 1 only**. Phases 2–4 are roadmap, not implemented now.
- Step 0 of implementation: copy this plan to `/Users/mrava87/Desktop/OpenSource/pylops-mcp/asession/InitialPlan.md` (create the `asession/` directory), then implement Phase 1.
