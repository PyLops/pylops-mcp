# PR 9: Generate indexes via a manual workflow; keep release builds clean

- URL: https://github.com/PyLops/pylops-mcp/pull/9
- Branch: index-workflow

## Why
The release job ran `make index-missing` before `uv build`, dirtying the tree. hatch-vcs then produced `0.1.1.dev0` / `0.2.1.dev0` instead of the tagged versions, so PyPI flagged them as pre-releases.

## What
- New `Update indexes` workflow (`workflow_dispatch`, optional PyLops version) that opens a PR with new index files.
- `release.yml` no longer generates indexes; it fails if any PyPI release (>= 2.4.0) lacks an index.
- README and `pyproject.toml` comment updated.

## Limitations / testing
- Workflow YAML parses; not yet run on GitHub.
- Needs "Allow GitHub Actions to create and approve pull requests" enabled; PRs from `GITHUB_TOKEN` don't trigger CI.
