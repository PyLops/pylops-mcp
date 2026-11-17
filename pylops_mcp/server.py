import difflib
import json
from functools import cache
from typing import Any

from mcp.server.mcpserver import MCPServer

from pylops_mcp.index import PACKAGES, available_versions, load_index
from pylops_mcp.introspect import Catalog

mcp = MCPServer("pylops")
POOL_KEYS = {
    "operator": "operators",
    "solver": "solvers",
    "workflow": "workflows",
    "proxoperator": "proxoperators",
    "proxsolver": "proxsolvers",
    "array": "arrays",
}
# search kinds -> (package, kind within that package's catalog)
SEARCH_KINDS = {
    "operator": ("pylops", "operator"),
    "solver": ("pylops", "solver"),
    "workflow": ("pylops", "workflow"),
    "proxoperator": ("pyproximal", "operator"),
    "proxsolver": ("pyproximal", "solver"),
    "mpioperator": ("pylops_mpi", "operator"),
    "mpisolver": ("pylops_mpi", "solver"),
    "mpiproxoperator": ("pylops_mpi", "proxoperator"),
    "mpiproxsolver": ("pylops_mpi", "proxsolver"),
    "mpiarray": ("pylops_mpi", "array"),
}


@cache
def _catalog(package: str, version: str | None) -> Catalog | None:
    """Catalog of a package version (None: latest), or None if it has no index."""
    try:
        return load_index(version, package)
    except KeyError:
        return None


def _unknown_version(package: str, version: str | None) -> dict[str, Any]:
    return {
        "error": f"No index for {package} version '{version}'",
        "available_versions": available_versions(package),
    }


def _lookup(
    package: str, kind: str, name: str, version: str | None = None
) -> dict[str, Any]:
    catalog = _catalog(package, version)
    if catalog is None:
        return _unknown_version(package, version)
    pool = catalog[POOL_KEYS[kind]]
    vkey = PACKAGES[package].version_key
    resolved = catalog[vkey]
    if name in pool:
        return {vkey: resolved, **pool[name]}
    lowered = {n.lower(): n for n in pool}
    if name.lower() in lowered:
        return {vkey: resolved, **pool[lowered[name.lower()]]}
    close = difflib.get_close_matches(name, list(pool), n=5, cutoff=0.5)
    return {
        vkey: resolved,
        "error": f"Unknown {package} {kind} '{name}'",
        "suggestions": close,
    }


def _list(
    package: str, kind: str, module: str | None, version: str | None
) -> dict[str, Any]:
    catalog = _catalog(package, version)
    if catalog is None:
        return _unknown_version(package, version)
    key = POOL_KEYS[kind]
    names = sorted(
        name
        for name, entry in catalog[key].items()
        if module is None or module in entry["module"]
    )
    return {
        PACKAGES[package].version_key: catalog[PACKAGES[package].version_key],
        key: names,
    }


@mcp.tool()
def list_versions() -> dict[str, Any]:
    """List the PyLops, PyProximal and PyLops-MPI versions that have an index.

    For each package the latest version is the default.
    """
    out: dict[str, Any] = {}
    for package, pkg in PACKAGES.items():
        catalog = _catalog(package, None)
        assert catalog is not None
        default = catalog[pkg.version_key]
        out[package] = {
            "default": default,
            "versions": available_versions(package) or [default],
        }
    return out


@mcp.tool()
def search(
    query: str,
    kind: str = "all",
    pylops_version: str | None = None,
    pyproximal_version: str | None = None,
    pylops_mpi_version: str | None = None,
) -> dict[str, Any]:
    """Search PyLops, PyProximal and PyLops-MPI by name or docstring summary.

    kind is one of "all", "operator", "solver", "workflow" (PyLops),
    "proxoperator", "proxsolver" (PyProximal) or "mpioperator", "mpisolver",
    "mpiproxoperator", "mpiproxsolver", "mpiarray" (PyLops-MPI).
    pylops_version, pyproximal_version and pylops_mpi_version select the
    versions (e.g. "2.6", "0.10", "0.6"); default is the latest.
    """
    versions = {
        "pylops": pylops_version,
        "pyproximal": pyproximal_version,
        "pylops_mpi": pylops_mpi_version,
    }
    q = query.lower()
    kinds = list(SEARCH_KINDS) if kind == "all" else [kind]
    out: dict[str, Any] = {}
    hits: list[dict[str, str]] = []
    for k in kinds:
        if k not in SEARCH_KINDS:
            continue
        package, pool_kind = SEARCH_KINDS[k]
        catalog = _catalog(package, versions[package])
        if catalog is None:
            return _unknown_version(package, versions[package])
        out[PACKAGES[package].version_key] = catalog[PACKAGES[package].version_key]
        for name, entry in catalog[POOL_KEYS[pool_kind]].items():
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
    return {**out, "results": hits[:20]}


@mcp.tool()
def list_operators(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List operator names, optionally filtered by module (e.g. "basicoperators").

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("pylops", "operator", module, pylops_version)


@mcp.tool()
def list_solvers(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List solver names, optionally filtered by module (e.g. "sparsity").

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("pylops", "solver", module, pylops_version)


@mcp.tool()
def list_workflows(
    module: str | None = None, pylops_version: str | None = None
) -> dict[str, Any]:
    """List workflow names (inversion/decomposition helpers), optionally by module.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _list("pylops", "workflow", module, pylops_version)


@mcp.tool()
def get_operator(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops operator.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("pylops", "operator", name, pylops_version)


@mcp.tool()
def get_solver(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops solver.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("pylops", "solver", name, pylops_version)


@mcp.tool()
def get_workflow(name: str, pylops_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops workflow.

    pylops_version selects the PyLops version (e.g. "2.6"); default is the latest.
    """
    return _lookup("pylops", "workflow", name, pylops_version)


@mcp.tool()
def list_proxperators(
    module: str | None = None, pyproximal_version: str | None = None
) -> dict[str, Any]:
    """List PyProximal proximal operator names, optionally filtered by module.

    pyproximal_version selects the PyProximal version (e.g. "0.10"); default is
    the latest.
    """
    return _list("pyproximal", "operator", module, pyproximal_version)


@mcp.tool()
def list_proxsolvers(
    module: str | None = None, pyproximal_version: str | None = None
) -> dict[str, Any]:
    """List PyProximal solver names, optionally filtered by module (e.g. "primal").

    pyproximal_version selects the PyProximal version (e.g. "0.10"); default is
    the latest.
    """
    return _list("pyproximal", "solver", module, pyproximal_version)


@mcp.tool()
def get_proxoperator(
    name: str, pyproximal_version: str | None = None
) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyProximal operator.

    pyproximal_version selects the PyProximal version (e.g. "0.10"); default is
    the latest.
    """
    return _lookup("pyproximal", "operator", name, pyproximal_version)


@mcp.tool()
def get_proxsolver(name: str, pyproximal_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyProximal solver.

    pyproximal_version selects the PyProximal version (e.g. "0.10"); default is
    the latest.
    """
    return _lookup("pyproximal", "solver", name, pyproximal_version)


@mcp.tool()
def list_mpioperators(
    module: str | None = None, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """List PyLops-MPI operator names, optionally by module (e.g. "signalprocessing").

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _list("pylops_mpi", "operator", module, pylops_mpi_version)


@mcp.tool()
def get_mpioperator(name: str, pylops_mpi_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops-MPI operator.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _lookup("pylops_mpi", "operator", name, pylops_mpi_version)


@mcp.tool()
def list_mpisolvers(
    module: str | None = None, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """List PyLops-MPI solver names, optionally by module (e.g. "optimization").

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _list("pylops_mpi", "solver", module, pylops_mpi_version)


@mcp.tool()
def get_mpisolver(name: str, pylops_mpi_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops-MPI solver.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _lookup("pylops_mpi", "solver", name, pylops_mpi_version)


@mcp.tool()
def list_mpiproxoperators(
    module: str | None = None, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """List PyLops-MPI proximal operator names, optionally filtered by module.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _list("pylops_mpi", "proxoperator", module, pylops_mpi_version)


@mcp.tool()
def get_mpiproxoperator(
    name: str, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops-MPI proximal operator.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _lookup("pylops_mpi", "proxoperator", name, pylops_mpi_version)


@mcp.tool()
def list_mpiproxsolvers(
    module: str | None = None, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """List PyLops-MPI proximal solver names, optionally filtered by module.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _list("pylops_mpi", "proxsolver", module, pylops_mpi_version)


@mcp.tool()
def get_mpiproxsolver(
    name: str, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops-MPI proximal solver.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _lookup("pylops_mpi", "proxsolver", name, pylops_mpi_version)


@mcp.tool()
def list_mpiarrays(
    module: str | None = None, pylops_mpi_version: str | None = None
) -> dict[str, Any]:
    """List PyLops-MPI array classes (DistributedArray, ...), optionally by module.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _list("pylops_mpi", "array", module, pylops_mpi_version)


@mcp.tool()
def get_mpiarray(name: str, pylops_mpi_version: str | None = None) -> dict[str, Any]:
    """Get signature, parameters, notes and examples of a PyLops-MPI array class.

    pylops_mpi_version selects the PyLops-MPI version (e.g. "0.6"); default is
    the latest.
    """
    return _lookup("pylops_mpi", "array", name, pylops_mpi_version)


@mcp.resource("pylops://operators/{name}")
def operator_resource(name: str) -> str:
    """Operator description (latest PyLops) as JSON."""
    return json.dumps(_lookup("pylops", "operator", name))


@mcp.resource("pylops://{pylops_version}/operators/{name}")
def versioned_operator_resource(pylops_version: str, name: str) -> str:
    """Operator description for a given PyLops version as JSON."""
    return json.dumps(_lookup("pylops", "operator", name, pylops_version))


@mcp.resource("pyproximal://operators/{name}")
def proxoperator_resource(name: str) -> str:
    """Proximal operator description (latest PyProximal) as JSON."""
    return json.dumps(_lookup("pyproximal", "operator", name))


@mcp.resource("pyproximal://{pyproximal_version}/operators/{name}")
def versioned_proxoperator_resource(pyproximal_version: str, name: str) -> str:
    """Proximal operator description for a given PyProximal version as JSON."""
    return json.dumps(_lookup("pyproximal", "operator", name, pyproximal_version))


@mcp.resource("pylops-mpi://operators/{name}")
def mpioperator_resource(name: str) -> str:
    """Operator description (latest PyLops-MPI) as JSON."""
    return json.dumps(_lookup("pylops_mpi", "operator", name))


@mcp.resource("pylops-mpi://{pylops_mpi_version}/operators/{name}")
def versioned_mpioperator_resource(pylops_mpi_version: str, name: str) -> str:
    """Operator description for a given PyLops-MPI version as JSON."""
    return json.dumps(_lookup("pylops_mpi", "operator", name, pylops_mpi_version))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
