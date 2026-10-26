import importlib
import inspect
import pkgutil
from typing import Any

import pylops
from numpydoc.docscrape import ClassDoc, FunctionDoc
from pylops import LinearOperator

Entry = dict[str, Any]
Catalog = dict[str, Any]

# Packages whose ``__all__`` is scanned for factory functions returning operators
PUBLIC_PACKAGES = (
    "pylops.basicoperators",
    "pylops.signalprocessing",
    "pylops.waveeqprocessing",
    "pylops.avo",
    "pylops.medical",
)
# Public functions/classes that run an inversion or decomposition, not operators
WORKFLOWS = {
    "MDD",
    "SeismicInterpolation",
    "WavefieldDecomposition",
    "Deghosting",
    "PoststackInversion",
    "PrestackInversion",
    "Marchenko",
    "LSM",
}


def describe(obj: Any, kind: str) -> Entry:
    """Return a structured description of an operator class or solver function."""
    doc = ClassDoc(obj) if inspect.isclass(obj) else FunctionDoc(obj)
    try:
        signature = str(inspect.signature(obj))
    except (TypeError, ValueError):
        signature = "(...)"
    return {
        "name": obj.__name__,
        "kind": kind,
        "module": obj.__module__,
        "signature": signature,
        "summary": " ".join(doc["Summary"]),
        "parameters": [
            {"name": p.name, "type": p.type, "desc": " ".join(p.desc)}
            for p in doc["Parameters"]
        ],
        "notes": "\n".join(doc["Notes"]),
        "examples": "\n".join(doc["Examples"]),
    }


def build_pylops_catalog() -> Catalog:
    """Introspect the installed PyLops and return its operators and solvers."""
    operators: dict[str, Entry] = {}
    solvers: dict[str, Entry] = {}
    for info in pkgutil.walk_packages(pylops.__path__, "pylops."):
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # optional dependencies may be missing
            continue
        for name, obj in vars(mod).items():
            if name.startswith("_") or not hasattr(obj, "__module__"):
                continue
            if not str(obj.__module__).startswith("pylops"):
                continue
            if (
                inspect.isclass(obj)
                and issubclass(obj, LinearOperator)
                and obj is not LinearOperator
            ):
                if name not in operators:
                    operators[name] = describe(obj, "operator")
            elif (
                inspect.isfunction(obj)
                and ".optimization." in obj.__module__
                and name.islower()
                and name not in solvers
            ):
                solvers[name] = describe(obj, "solver")
    workflows: dict[str, Entry] = {}
    for pkg_name in PUBLIC_PACKAGES:
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError:  # package absent in older PyLops
            continue
        for name in getattr(pkg, "__all__", []):
            obj = getattr(pkg, name, None)
            is_op_class = inspect.isclass(obj) and issubclass(obj, LinearOperator)
            if is_op_class or not (inspect.isfunction(obj) or inspect.isclass(obj)):
                continue  # operator classes are collected by the module walk above
            if name in WORKFLOWS:
                workflows.setdefault(name, describe(obj, "workflow"))
            else:
                operators.setdefault(name, describe(obj, "operator"))
    return {
        "pylops_version": pylops.__version__,
        "operators": operators,
        "solvers": solvers,
        "workflows": workflows,
    }


def build_pyproximal_catalog() -> Catalog:
    """Introspect the installed PyProximal and return its operators and solvers."""
    import pyproximal
    import pyproximal.optimization
    import pyproximal.proximal

    operators: dict[str, Entry] = {}
    for name in pyproximal.proximal.__all__:
        obj = getattr(pyproximal.proximal, name, None)
        if inspect.isclass(obj) or inspect.isfunction(obj):  # Simplex is a function
            operators[name] = describe(obj, "operator")
    solvers: dict[str, Entry] = {}
    opt = pyproximal.optimization
    for info in pkgutil.walk_packages(opt.__path__, "pyproximal.optimization."):
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # optional dependencies may be missing
            continue
        for name, obj in vars(mod).items():
            if (
                not name.startswith("_")
                and inspect.isfunction(obj)
                and obj.__module__ == info.name
            ):
                solvers.setdefault(name, describe(obj, "solver"))
    return {
        "pyproximal_version": pyproximal.__version__,
        "operators": operators,
        "solvers": solvers,
    }
