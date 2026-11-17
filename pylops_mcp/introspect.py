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
# Packages whose ``__all__`` lists the PyLops-MPI operators (classes and factories)
MPI_PUBLIC_PACKAGES = (
    "pylops_mpi.basicoperators",
    "pylops_mpi.signalprocessing",
    "pylops_mpi.waveeqprocessing",
)
# Core PyLops-MPI classes needed to build the inputs of operators and solvers
ARRAY_CLASSES = ("DistributedArray", "StackedDistributedArray", "Partition")
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


def build_pylops_mpi_catalog() -> Catalog:
    """Introspect the installed PyLops-MPI and return its catalog.

    Pools: operators, solvers, proxoperators, proxsolvers (the last two are
    empty in releases without ``pylops_mpi.proximal``) and arrays.
    """
    import pylops_mpi

    bases = tuple(
        b
        for b in (
            getattr(pylops_mpi, "MPILinearOperator", None),
            getattr(pylops_mpi, "MPIStackedLinearOperator", None),
        )
        if b is not None
    )
    operators: dict[str, Entry] = {}
    solvers: dict[str, Entry] = {}
    for info in pkgutil.walk_packages(pylops_mpi.__path__, "pylops_mpi."):
        if ".proximal" in info.name:  # indexed separately below
            continue
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # optional dependencies may be missing
            continue
        for name, obj in vars(mod).items():
            if name.startswith("_") or not hasattr(obj, "__module__"):
                continue
            if not str(obj.__module__).startswith("pylops_mpi"):
                continue
            if inspect.isclass(obj) and issubclass(obj, bases) and obj not in bases:
                operators.setdefault(name, describe(obj, "operator"))
            elif (
                inspect.isfunction(obj)
                and ".optimization." in obj.__module__
                and not obj.__module__.endswith(".utils")
                and name.islower()
            ):
                solvers.setdefault(name, describe(obj, "solver"))
    for pkg_name in MPI_PUBLIC_PACKAGES:  # factory functions (e.g. MPIMDC)
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError:
            continue
        for name in getattr(pkg, "__all__", []):
            obj = getattr(pkg, name, None)
            if inspect.isfunction(obj) or inspect.isclass(obj):
                operators.setdefault(name, describe(obj, "operator"))

    proxoperators: dict[str, Entry] = {}
    proxsolvers: dict[str, Entry] = {}
    try:
        import pylops_mpi.proximal as mpiprox
        import pylops_mpi.proximal.optimization as mpiproxopt
        import pylops_mpi.proximal.proximal as mpiproxprox
    except ImportError:  # proximal module absent in older releases
        pass
    else:
        names = [*mpiprox.__all__, *mpiproxprox.__all__]
        for name in names:
            obj = getattr(mpiprox, name, None)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                proxoperators[name] = describe(obj, "operator")
        for name in mpiproxopt.__all__:
            obj = getattr(mpiproxopt, name, None)
            if inspect.isfunction(obj):
                proxsolvers[name] = describe(obj, "solver")

    arrays: dict[str, Entry] = {}
    for name in ARRAY_CLASSES:
        obj = getattr(pylops_mpi, name, None)
        if inspect.isclass(obj):
            arrays[name] = describe(obj, "array")
    return {
        "pylops_mpi_version": pylops_mpi.__version__,
        "operators": operators,
        "solvers": solvers,
        "proxoperators": proxoperators,
        "proxsolvers": proxsolvers,
        "arrays": arrays,
    }
