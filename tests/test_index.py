import importlib
import inspect
import json
from pathlib import Path

import pytest

from pylops_mcp.index import (
    PACKAGES,
    available_versions,
    load_index,
    resolve_version,
    write_index,
)
from pylops_mcp.introspect import (
    MPI_PUBLIC_PACKAGES,
    PUBLIC_PACKAGES,
    build_pylops_catalog,
    build_pylops_mpi_catalog,
    build_pyproximal_catalog,
)


def test_roundtrip(tmp_path: Path) -> None:
    built = write_index(
        "pylops", tmp_path / f"{build_pylops_catalog()['pylops_version']}.json"
    )
    assert load_index(index_dir=tmp_path) == built
    assert built["operators"] and built["solvers"] and built["workflows"]


def test_public_api_is_complete() -> None:
    cat = build_pylops_catalog()
    indexed = set(cat["operators"]) | set(cat["workflows"])
    for pkg_name in PUBLIC_PACKAGES:
        pkg = importlib.import_module(pkg_name)
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                assert name in indexed, f"{pkg_name}.{name} missing from index"


def test_factory_functions_and_workflows() -> None:
    cat = build_pylops_catalog()
    for name in (
        "Restriction",
        "FFT",
        "Radon2D",
        "MDC",
        "PoststackLinearModelling",
        "CT2D",
    ):
        assert name in cat["operators"]
    for name in ("MDD", "PrestackInversion", "Marchenko", "LSM"):
        assert name in cat["workflows"]
        assert name not in cat["operators"]
    assert "zoeppritz_scattering" not in cat["operators"]
    assert "zoeppritz_scattering" not in cat["workflows"]


def _fake_dir(tmp_path: Path, versions: list[str]) -> Path:
    for v in versions:
        (tmp_path / f"{v}.json").write_text(json.dumps({"pylops_version": v}))
    return tmp_path


def test_version_ordering_and_default(tmp_path: Path) -> None:
    d = _fake_dir(tmp_path, ["2.9.0", "2.10.0", "2.4.0"])
    assert available_versions(index_dir=d) == ["2.4.0", "2.9.0", "2.10.0"]
    assert resolve_version(None, index_dir=d) == "2.10.0"


def test_version_prefix_and_unknown(tmp_path: Path) -> None:
    d = _fake_dir(tmp_path, ["2.8.0", "2.8.1", "2.9.0"])
    assert resolve_version("2.8", index_dir=d) == "2.8.1"
    assert resolve_version("v2.9.0", index_dir=d) == "2.9.0"
    assert resolve_version("2.7", index_dir=d) is None
    with pytest.raises(KeyError):
        load_index("2.7", index_dir=d)


@pytest.mark.parametrize("package", list(PACKAGES))
def test_committed_indexes_match_filenames(package: str) -> None:
    pkg = PACKAGES[package]
    versions = available_versions(package)
    assert versions
    for v in versions:
        index = json.loads((pkg.index_dir / f"{v}.json").read_text())
        assert index[pkg.version_key] == v


def test_pyproximal_roundtrip(tmp_path: Path) -> None:
    version = build_pyproximal_catalog()["pyproximal_version"]
    built = write_index("pyproximal", tmp_path / f"{version}.json")
    assert load_index(package="pyproximal", index_dir=tmp_path) == built
    assert built["operators"] and built["solvers"]


def test_pyproximal_api_is_complete() -> None:
    import pyproximal.optimization.primal as primal
    import pyproximal.proximal as proximal

    cat = build_pyproximal_catalog()
    assert set(proximal.__all__) <= set(cat["operators"])
    for name in ("ProximalGradient", "ADMM", "LinearizedADMM", "HQS"):
        assert hasattr(primal, name)
        assert name in cat["solvers"]
    assert {"PrimalDual", "PALM", "PlugAndPlay", "Bregman"} <= set(cat["solvers"])
    # a name can be both operator and solver (e.g. RED in newer releases)
    for name in set(cat["operators"]) & set(cat["solvers"]):
        assert cat["operators"][name]["module"] != cat["solvers"][name]["module"]


def _require_pylops_mpi() -> None:
    """Skip if PyLops-MPI (or the MPI library it needs) is not available."""
    try:
        import pylops_mpi  # noqa: F401
    except (ImportError, RuntimeError) as e:  # mpi4py raises RuntimeError
        pytest.skip(f"pylops_mpi not importable: {e}"[:200])


def test_pylops_mpi_roundtrip(tmp_path: Path) -> None:
    _require_pylops_mpi()
    version = build_pylops_mpi_catalog()["pylops_mpi_version"]
    built = write_index("pylops_mpi", tmp_path / f"{version}.json")
    assert load_index(package="pylops_mpi", index_dir=tmp_path) == built
    assert built["operators"] and built["solvers"] and built["arrays"]


def test_pylops_mpi_api_is_complete() -> None:
    _require_pylops_mpi()
    cat = build_pylops_mpi_catalog()
    for pkg_name in MPI_PUBLIC_PACKAGES:
        pkg = importlib.import_module(pkg_name)
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                assert name in cat["operators"], f"{pkg_name}.{name} missing"
    assert {"cg", "cgls", "ista", "fista"} <= set(cat["solvers"])
    assert not {"first_distarray", "CGLS"} & set(cat["solvers"])
    assert {"DistributedArray", "StackedDistributedArray"} <= set(cat["arrays"])
