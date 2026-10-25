from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pylops-mcp")
except PackageNotFoundError:
    __version__ = "unknown"
