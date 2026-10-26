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
    PUBLIC_PACKAGES,
    build_pylops_catalog,
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
    # RED is both a proximal operator and a solver, kept in separate pools
    assert cat["operators"]["RED"]["module"] != cat["solvers"]["RED"]["module"]
