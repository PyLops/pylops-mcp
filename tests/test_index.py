from pathlib import Path

from pylops_mcp.index import load_index, write_index


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "data" / "index.json"
    built = write_index(path)
    assert load_index(path) == built
    assert built["operators"] and built["solvers"]
