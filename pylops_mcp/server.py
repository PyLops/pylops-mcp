import difflib
from typing import Any

from mcp.server.mcpserver import MCPServer

from pylops_mcp.index import load_index

mcp = MCPServer("pylops")
CATALOG = load_index()
POOLS: dict[str, dict[str, Any]] = {
    "operator": CATALOG["operators"],
    "solver": CATALOG["solvers"],
    "workflow": CATALOG["workflows"],
}


def _lookup(kind: str, name: str) -> dict[str, Any]:
    pool = POOLS[kind]
    version = CATALOG["pylops_version"]
    if name in pool:
        return {"pylops_version": version, **pool[name]}
    lowered = {n.lower(): n for n in pool}
    if name.lower() in lowered:
        return {"pylops_version": version, **pool[lowered[name.lower()]]}
    close = difflib.get_close_matches(name, list(pool), n=5, cutoff=0.5)
    return {
        "pylops_version": version,
        "error": f"Unknown {kind} '{name}'",
        "suggestions": close,
    }


@mcp.tool()
def search(query: str, kind: str = "all") -> dict[str, Any]:
    """Search PyLops operators, solvers and workflows by name or docstring summary.

    kind is one of "all", "operator", "solver" or "workflow".
    """
    q = query.lower()
    kinds = list(POOLS) if kind == "all" else [kind]
    hits: list[dict[str, str]] = []
    for k in kinds:
        for name, entry in POOLS.get(k, {}).items():
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
    return {"pylops_version": CATALOG["pylops_version"], "results": hits[:20]}


@mcp.tool()
def list_operators(module: str | None = None) -> dict[str, Any]:
    """List operator names, optionally filtered by module (e.g. "basicoperators")."""
    names = sorted(
        name
        for name, entry in CATALOG["operators"].items()
        if module is None or module in entry["module"]
    )
    return {"pylops_version": CATALOG["pylops_version"], "operators": names}


@mcp.tool()
def list_solvers(module: str | None = None) -> dict[str, Any]:
    """List solver names, optionally filtered by module (e.g. "sparsity")."""
    names = sorted(
        name
        for name, entry in CATALOG["solvers"].items()
        if module is None or module in entry["module"]
    )
    return {"pylops_version": CATALOG["pylops_version"], "solvers": names}


@mcp.tool()
def list_workflows(module: str | None = None) -> dict[str, Any]:
    """List workflow names (inversion/decomposition helpers), optionally by module."""
    names = sorted(
        name
        for name, entry in CATALOG["workflows"].items()
        if module is None or module in entry["module"]
    )
    return {"pylops_version": CATALOG["pylops_version"], "workflows": names}


@mcp.tool()
def get_operator(name: str) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops operator."""
    return _lookup("operator", name)


@mcp.tool()
def get_solver(name: str) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops solver."""
    return _lookup("solver", name)


@mcp.tool()
def get_workflow(name: str) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops workflow."""
    return _lookup("workflow", name)


@mcp.resource("pylops://operators/{name}")
def operator_resource(name: str) -> str:
    """Operator description as text."""
    return str(_lookup("operator", name))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
