import difflib
import json
from functools import cache
from typing import Any

from mcp.server.mcpserver import MCPServer

from pylops_mcp.index import available_versions, load_index
from pylops_mcp.introspect import Catalog

mcp = MCPServer("pylops")
POOL_KEYS = {"operator": "operators", "solver": "solvers", "workflow": "workflows"}


@cache
def _catalog(version: str | None) -> Catalog | None:
    """Catalog of a PyLops version (None: latest), or None if it has no index."""
    try:
        return load_index(version)
    except KeyError:
        return None


def _unknown_version(version: str | None) -> dict[str, Any]:
    return {
        "error": f"No index for PyLops version '{version}'",
        "available_versions": available_versions(),
    }


def _lookup(kind: str, name: str, version: str | None = None) -> dict[str, Any]:
    catalog = _catalog(version)
    if catalog is None:
        return _unknown_version(version)
    pool = catalog[POOL_KEYS[kind]]
    resolved = catalog["pylops_version"]
    if name in pool:
        return {"pylops_version": resolved, **pool[name]}
    lowered = {n.lower(): n for n in pool}
    if name.lower() in lowered:
        return {"pylops_version": resolved, **pool[lowered[name.lower()]]}
    close = difflib.get_close_matches(name, list(pool), n=5, cutoff=0.5)
    return {
        "pylops_version": resolved,
        "error": f"Unknown {kind} '{name}'",
        "suggestions": close,
    }


def _list(kind: str, module: str | None, version: str | None) -> dict[str, Any]:
    catalog = _catalog(version)
    if catalog is None:
        return _unknown_version(version)
    key = POOL_KEYS[kind]
    names = sorted(
        name
        for name, entry in catalog[key].items()
        if module is None or module in entry["module"]
    )
    return {"pylops_version": catalog["pylops_version"], key: names}


@mcp.tool()
def list_versions() -> dict[str, Any]:
    """List the PyLops versions that have an index; the latest is the default."""
    catalog = _catalog(None)
    assert catalog is not None
    return {
        "default": catalog["pylops_version"],
        "versions": available_versions() or [catalog["pylops_version"]],
    }


@mcp.tool()
def search(
    query: str, kind: str = "all", pylops_version: str | None = None
) -> dict[str, Any]:
    """Search PyLops operators, solvers and workflows by name or docstring summary.

    kind is one of "all", "operator", "solver" or "workflow".
    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    catalog = _catalog(pylops_version)
    if catalog is None:
        return _unknown_version(pylops_version)
    q = query.lower()
    kinds = list(POOL_KEYS) if kind == "all" else [kind]
    hits: list[dict[str, str]] = []
    for k in kinds:
        for name, entry in catalog.get(POOL_KEYS.get(k, ""), {}).items():
            if q in name.lower() or q in entry["summary"].lower():
                hits.append(
                    {
                        "name": name,
                        "kind": k,
                        "module": entry["module"],
                        "summary": entry["summary"],
                    }
                )
    hits.sort(key=lambda h: (q not in h["name"].lower(), h["name"]))
    return {"pylops_version": catalog["pylops_version"], "results": hits[:20]}


@mcp.tool()
def list_operators(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List operator names, optionally filtered by module (e.g. "basicoperators").

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("operator", module, pylops_version)


@mcp.tool()
def list_solvers(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List solver names, optionally filtered by module (e.g. "sparsity").

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("solver", module, pylops_version)


@mcp.tool()
def list_workflows(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List workflow names (inversion/decomposition helpers), optionally by module.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("workflow", module, pylops_version)


@mcp.tool()
def get_operator(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops operator.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("operator", name, pylops_version)


@mcp.tool()
def get_solver(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops solver.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("solver", name, pylops_version)


@mcp.tool()
def get_workflow(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops workflow.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("workflow", name, pylops_version)


@mcp.resource("pylops://operators/{name}")
def operator_resource(name: str) -> str:
    """Operator description (latest PyLops) as JSON."""
    return json.dumps(_lookup("operator", name))


@mcp.resource("pylops://{pylops_version}/operators/{name}")
def versioned_operator_resource(pylops_version: str, name: str) -> str:
    """Operator description for a given PyLops version as JSON."""
    return json.dumps(_lookup("operator", name, pylops_version))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
