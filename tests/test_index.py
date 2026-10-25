import importlib
import inspect
from pathlib import Path

from pylops import LinearOperator

from pylops_mcp.index import load_index, write_index
from pylops_mcp.introspect import PUBLIC_PACKAGES, build_catalog


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "data" / "index.json"
    built = write_index(path)
    assert load_index(path) == built
    assert built["operators"] and built["solvers"] and built["workflows"]


def test_public_api_is_complete() -> None:
    cat = build_catalog()
    indexed = set(cat["operators"]) | set(cat["workflows"])
    for pkg_name in PUBLIC_PACKAGES:
        pkg = importlib.import_module(pkg_name)
        for name in pkg.__all__:
            obj = getattr(pkg, name)
            is_op = inspect.isclass(obj) and issubclass(obj, LinearOperator)
            if is_op or inspect.isfunction(obj):
                assert name in indexed, f"{pkg_name}.{name} missing from index"


def test_factory_functions_and_workflows() -> None:
    cat = build_catalog()
    for name in ("Restriction", "FFT", "Radon2D", "MDC", "PoststackLinearModelling"):
        assert name in cat["operators"]
    for name in ("MDD", "PrestackInversion"):
        assert name in cat["workflows"]
        assert name not in cat["operators"]
    assert "zoeppritz_scattering" not in cat["operators"]
    assert "zoeppritz_scattering" not in cat["workflows"]
