# PyLops-MCP

[![PyPI](https://img.shields.io/pypi/v/pylops-mcp)](https://pypi.org/project/pylops-mcp/)

MCP server exposing [PyLops](https://pylops.readthedocs.io) operators and solvers
in a structured way, so agents and users can query them instead of web searching
or crawling files. 

The catalog is built by introspecting the installed PyLops
(numpydoc) and dumped to one file per PyLops release, `pylops_mcp/data/indexes/<version>.json`
(`make index`; releases from 2.4.0 are shipped).

## Tools

| Tool | Arguments | Description |
| --- | --- | --- |
| `list_versions` | none | PyLops versions that have an index, and the default (the latest). |
| `search` | `query` (str), `kind` (`"all"` \| `"operator"` \| `"solver"` \| `"workflow"`, default `"all"`), `pylops_version` (str, optional) | Case-insensitive substring search over names and docstring summaries. Returns up to 20 hits (`name`, `kind`, `module`, `summary`), name matches first. |
| `list_operators` | `module` (str, optional, e.g. `"basicoperators"`), `pylops_version` (str, optional) | Sorted list of operator names, optionally filtered by module. |
| `list_solvers` | `module` (str, optional, e.g. `"sparsity"`), `pylops_version` (str, optional) | Sorted list of solver names, optionally filtered by module. |
| `list_workflows` | `module` (str, optional), `pylops_version` (str, optional) | Sorted list of workflow names (inversion/decomposition helpers such as `MDD`, `PrestackInversion`), optionally filtered by module. |
| `get_operator` | `name` (str), `pylops_version` (str, optional) | Signature, parameters, notes and examples of an operator. Lookup is case-insensitive. |
| `get_solver` | `name` (str), `pylops_version` (str, optional) | Signature, parameters, notes and examples of a solver. Lookup is case-insensitive. |
| `get_workflow` | `name` (str), `pylops_version` (str, optional) | Signature, parameters, notes and examples of a workflow. Lookup is case-insensitive. |

Every tool except `list_versions` takes an optional `pylops_version` (e.g. `"2.6"`,
resolved to the highest matching release; default: the latest). An unknown version
returns an `error` with the `available_versions`. All responses include the
resolved `pylops_version`. An unknown name returns an `error`
together with up to 5 close-match `suggestions`.

Operator descriptions are also exposed as the MCP resource
`pylops://operators/{name}` (latest) and `pylops://{pylops_version}/operators/{name}`.


## Installation

### For Users

No clone or index build is needed: the PyPI release ships prebuilt indexes
for PyLops 2.4.0 and later (CI builds any missing release at release time).

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

**Codex:**

```
codex mcp add pylops -- uvx pylops-mcp
```

or add to `~/.codex/config.toml`:

```toml
[mcp_servers.pylops]
command = "uvx"
args = ["pylops-mcp"]
```

**OpenCode:** add to `opencode.json` (project) or
`~/.config/opencode/opencode.json` (global):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "pylops": { "type": "local", "command": ["uvx", "pylops-mcp"], "enabled": true }
  }
}
```

**PI:** PI has no built-in MCP support, so first install the
[`pi-mcp-adapter`](https://pi.dev/packages/pi-mcp-adapter) extension:

```
pi install npm:pi-mcp-adapter
```

then add to `~/.pi/agent/mcp.json` (global) or `.pi/mcp.json` (project):

```json
{
  "mcpServers": {
    "pylops": { "command": "uvx", "args": ["pylops-mcp"] }
  }
}
```

### For Developers

This project is developed with Claude Code, so all the commands below are for
Claude Code only. For other clients, translate the `uv run ...` command into
that client's MCP configuration (see [For Users](#for-users)).

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

Running `make index` upfront is optional: the repository ships prebuilt
indexes in `pylops_mcp/data/indexes/`, and if there are none the server falls
back to introspecting the installed PyLops live at every startup (slower).

- `make index` indexes the PyLops installed in the project environment.
- `make index-all VERSIONS="2.4.0 2.5.0"` builds specific releases, each in an isolated environment.
- `make index-missing` builds every PyPI release (>= 2.4.0) that has no index yet.

The same can be done without a local setup via the *Update indexes* GitHub Action
(Actions tab, *Run workflow*; optionally give a PyLops version), which opens a PR with the new index files.
The release workflow does not generate indexes, so merge that PR before tagging.

Indexes of released versions are kept as they are; rebuild one only if you
change the introspection code.

## Releasing

Versions come from git tags (`hatch-vcs`):

- dry run: Actions → Release → *Run workflow* → `testpypi`
- release: Releases → *Draft a new release* → create tag → *Publish release* (publishes to PyPI)
