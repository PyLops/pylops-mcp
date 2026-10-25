# PyLops-MCP

[![PyPI](https://img.shields.io/pypi/v/pylops-mcp)](https://pypi.org/project/pylops-mcp/)

MCP server exposing [PyLops](https://pylops.readthedocs.io) operators and solvers
in a structured way, so agents and users can query them instead of web searching
or crawling files. 

The catalog is built by introspecting the installed PyLops
(numpydoc) and dumped to `pylops_mcp/data/index.json` (`make index`).

## Tools

| Tool | Arguments | Description |
| --- | --- | --- |
| `search` | `query` (str), `kind` (`"all"` \| `"operator"` \| `"solver"`, default `"all"`) | Case-insensitive substring search over names and docstring summaries. Returns up to 20 hits (`name`, `kind`, `module`, `summary`), name matches first. |
| `list_operators` | `module` (str, optional, e.g. `"basicoperators"`) | Sorted list of operator names, optionally filtered by module. |
| `list_solvers` | `module` (str, optional, e.g. `"sparsity"`) | Sorted list of solver names, optionally filtered by module. |
| `get_operator` | `name` (str) | Signature, parameters, notes and examples of an operator. Lookup is case-insensitive. |
| `get_solver` | `name` (str) | Signature, parameters, notes and examples of a solver. Lookup is case-insensitive. |

All responses include `pylops_version`. An unknown name returns an `error`
together with up to 5 close-match `suggestions`.

Operator descriptions are also exposed as the MCP resource
`pylops://operators/{name}`.


## Installation

### For Users

No clone or index build is needed: the PyPI release ships a prebuilt `index.json`
(rebuilt by CI against the latest PyLops at release time).

**Claude Code:**

```
claude mcp add --scope user pylops -- uvx pylops-mcp
```

**Claude Desktop:** add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pylops": { "command": "uvx", "args": ["pylops-mcp"] }
  }
}
```

### For Developers

Clone the repository first; the commands below assume it lives at `/path/to/pylops-mcp`.

#### 1. This project only

Run from inside the repository folder. The server is registered for this
project only (`--scope local`, the default), and `uv run` uses the project's
`.venv`. Nothing is installed globally.

```
claude mcp add pylops -- uv run pylops-mcp
```

#### 2. All projects, running from source

Register the server for every project and tell `uv` where the project lives, so
it works from any folder and always runs your current source:

```
claude mcp add --scope user pylops -- uv run --directory /path/to/pylops-mcp pylops-mcp
```

#### 3. All projects, as a global tool

Install `pylops-mcp` as a standalone tool and register the plain command
(add `-e` to the install to pick up source changes without reinstalling):

```
uv tool install /path/to/pylops-mcp
claude mcp add --scope user pylops -- pylops-mcp
```

#### Rebuilding the index

Running `make index` upfront is optional: the repository ships a prebuilt
`index.json`, and if it is missing the server falls back to introspecting
PyLops live at every startup (slower). Rebuild it with `make index` whenever
you change the introspection code or upgrade PyLops, so the served docs match
the installed version.

## Releasing

Versions come from git tags (`hatch-vcs`):

- dry run: Actions → Release → *Run workflow* → `testpypi`
- release: `git tag v0.1.0 && git push origin v0.1.0` (publishes to PyPI)
