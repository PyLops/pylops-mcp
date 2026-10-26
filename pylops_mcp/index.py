import argparse
import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from packaging.version import InvalidVersion, Version

from pylops_mcp.introspect import (
    Catalog,
    build_pylops_catalog,
    build_pyproximal_catalog,
)

INDEX_ROOT = Path(__file__).parent / "data" / "indexes"


@dataclass(frozen=True)
class Package:
    """A documented library that gets one index file per release."""

    name: str
    min_version: Version  # oldest release that gets an index
    build: Callable[[], Catalog]

    @property
    def index_dir(self) -> Path:
        return INDEX_ROOT / self.name

    @property
    def version_key(self) -> str:
        return f"{self.name}_version"

    @property
    def pypi_url(self) -> str:
        return f"https://pypi.org/pypi/{self.name}/json"


PACKAGES = {
    "pylops": Package("pylops", Version("2.4.0"), build_pylops_catalog),
    "pyproximal": Package("pyproximal", Version("0.9.0"), build_pyproximal_catalog),
}


def write_index(package: str = "pylops", path: Path | None = None) -> Catalog:
    """Build the catalog from the installed package and dump it to JSON.

    By default the file is ``indexes/<package>/<package version>.json``.
    """
    pkg = PACKAGES[package]
    catalog = pkg.build()
    path = path or pkg.index_dir / f"{catalog[pkg.version_key]}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=1))
    return catalog


def available_versions(
    package: str = "pylops", index_dir: Path | None = None
) -> list[str]:
    """Versions with a prebuilt index, oldest first."""
    index_dir = index_dir or PACKAGES[package].index_dir
    versions = []
    for p in index_dir.glob("*.json"):
        try:
            Version(p.stem)
        except InvalidVersion:
            continue
        versions.append(p.stem)
    return sorted(versions, key=Version)


def resolve_version(
    version: str | None, package: str = "pylops", index_dir: Path | None = None
) -> str | None:
    """Map a requested version to an available one.

    ``None`` gives the latest. An exact match wins, otherwise a prefix such as
    "2.8" gives the highest "2.8.x". Returns None when nothing matches.
    """
    versions = available_versions(package, index_dir)
    if not versions:
        return None
    if version is None:
        return versions[-1]
    version = version.strip().removeprefix("v")
    if version in versions:
        return version
    matches = [v for v in versions if v.startswith(version + ".")]
    return matches[-1] if matches else None


def load_index(
    version: str | None = None,
    package: str = "pylops",
    index_dir: Path | None = None,
) -> Catalog:
    """Load a prebuilt index, falling back to live introspection if there is none.

    Raises ``KeyError`` if prebuilt indexes exist but not for ``version``.
    """
    pkg = PACKAGES[package]
    index_dir = index_dir or pkg.index_dir
    if not available_versions(package, index_dir):
        return pkg.build()
    resolved = resolve_version(version, package, index_dir)
    if resolved is None:
        raise KeyError(version)
    catalog: Catalog = json.loads((index_dir / f"{resolved}.json").read_text())
    return catalog


def missing_versions(
    package: str = "pylops", index_dir: Path | None = None
) -> list[str]:
    """Final releases on PyPI (>= the package's minimum) without a prebuilt index."""
    pkg = PACKAGES[package]
    with urllib.request.urlopen(pkg.pypi_url, timeout=30) as resp:  # noqa: S310
        releases = json.load(resp)["releases"]
    have = set(available_versions(package, index_dir))
    found = []
    for v in releases:
        try:
            parsed = Version(v)
        except InvalidVersion:
            continue
        if parsed >= pkg.min_version and not parsed.is_prerelease and v not in have:
            found.append(v)
    return sorted(found, key=Version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", choices=PACKAGES, default="pylops")
    parser.add_argument("--out", type=Path, help="output file (default: indexes/)")
    parser.add_argument(
        "--missing", action="store_true", help="print versions lacking an index"
    )
    args = parser.parse_args()
    if args.missing:
        print("\n".join(missing_versions(args.package)))
    else:
        cat = write_index(args.package, args.out)
        counts = ", ".join(
            f"{len(v)} {k}" for k, v in cat.items() if isinstance(v, dict)
        )
        print(f"{args.package} {cat[PACKAGES[args.package].version_key]}: {counts}")
