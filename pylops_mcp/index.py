import argparse
import json
import urllib.request
from pathlib import Path

from packaging.version import InvalidVersion, Version

from pylops_mcp.introspect import Catalog, build_catalog

INDEX_DIR = Path(__file__).parent / "data" / "indexes"
MIN_VERSION = Version("2.4.0")  # oldest PyLops release that gets an index
PYPI_URL = "https://pypi.org/pypi/pylops/json"


def write_index(path: Path | None = None) -> Catalog:
    """Build the catalog from the installed PyLops and dump it to JSON.

    By default the file is ``indexes/<pylops version>.json``.
    """
    catalog = build_catalog()
    path = path or INDEX_DIR / f"{catalog['pylops_version']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=1))
    return catalog


def available_versions(index_dir: Path = INDEX_DIR) -> list[str]:
    """Versions with a prebuilt index, oldest first."""
    versions = []
    for p in index_dir.glob("*.json"):
        try:
            Version(p.stem)
        except InvalidVersion:
            continue
        versions.append(p.stem)
    return sorted(versions, key=Version)


def resolve_version(version: str | None, index_dir: Path = INDEX_DIR) -> str | None:
    """Map a requested version to an available one.

    ``None`` gives the latest. An exact match wins, otherwise a prefix such as
    "2.8" gives the highest "2.8.x". Returns None when nothing matches.
    """
    versions = available_versions(index_dir)
    if not versions:
        return None
    if version is None:
        return versions[-1]
    version = version.strip().removeprefix("v")
    if version in versions:
        return version
    matches = [v for v in versions if v.startswith(version + ".")]
    return matches[-1] if matches else None


def load_index(version: str | None = None, index_dir: Path = INDEX_DIR) -> Catalog:
    """Load a prebuilt index, falling back to live introspection if there is none.

    Raises ``KeyError`` if prebuilt indexes exist but not for ``version``.
    """
    if not available_versions(index_dir):
        return build_catalog()
    resolved = resolve_version(version, index_dir)
    if resolved is None:
        raise KeyError(version)
    catalog: Catalog = json.loads((index_dir / f"{resolved}.json").read_text())
    return catalog


def missing_versions(index_dir: Path = INDEX_DIR) -> list[str]:
    """Final PyLops releases on PyPI (>= MIN_VERSION) without a prebuilt index."""
    with urllib.request.urlopen(PYPI_URL, timeout=30) as resp:  # noqa: S310
        releases = json.load(resp)["releases"]
    have = set(available_versions(index_dir))
    found = []
    for v in releases:
        try:
            parsed = Version(v)
        except InvalidVersion:
            continue
        if parsed >= MIN_VERSION and not parsed.is_prerelease and v not in have:
            found.append(v)
    return sorted(found, key=Version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="output file (default: indexes/)")
    parser.add_argument(
        "--missing", action="store_true", help="print versions lacking an index"
    )
    args = parser.parse_args()
    if args.missing:
        print("\n".join(missing_versions()))
    else:
        cat = write_index(args.out)
        print(
            f"PyLops {cat['pylops_version']}: {len(cat['operators'])} operators, "
            f"{len(cat['solvers'])} solvers, {len(cat['workflows'])} workflows"
        )
