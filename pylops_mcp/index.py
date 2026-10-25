import json
from pathlib import Path

from pylops_mcp.introspect import Catalog, build_catalog

INDEX_PATH = Path(__file__).parent / "data" / "index.json"


def write_index(path: Path = INDEX_PATH) -> Catalog:
    """Build the catalog from the installed PyLops and dump it to JSON."""
    catalog = build_catalog()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=1))
    return catalog


def load_index(path: Path = INDEX_PATH) -> Catalog:
    """Load the prebuilt index, falling back to live introspection."""
    if path.exists():
        catalog: Catalog = json.loads(path.read_text())
        return catalog
    return build_catalog()


if __name__ == "__main__":
    cat = write_index()
    print(
        f"PyLops {cat['pylops_version']}: {len(cat['operators'])} operators, "
        f"{len(cat['solvers'])} solvers, {len(cat['workflows'])} workflows "
        f"-> {INDEX_PATH}"
    )
