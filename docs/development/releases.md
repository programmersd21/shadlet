# releases

shadlet uses semantic versioning.

## release checklist

1. update `__version__` in `packages/python/shadlet/version.py`; this is the
   single source of truth for the runtime, CLI, and `App` default version.
2. update `version` in `pyproject.toml`, `packages/renderer/package.json`, and
   the renderer lockfile.
3. update `CHANGELOG.md` and `docs/changelog.md`.
4. rebuild the renderer with `npm run build`.
5. run the full check suite:
   - `uv run ruff check packages/python tests`
   - `uv run ruff format --check packages/python tests`
   - `uv run mypy .`
   - `uv run pyright .`
   - `uv run pytest -q`
   - `cd packages/renderer && npm run lint && npm run format:check && npm run typecheck && npm run test && npm run build`
   - `uv build`
6. install the built wheel in a clean virtual environment and verify that
   `shadlet/web/static/index.html` and its assets are present.
7. Review and commit the release changes. Create a `vX.Y.Z` tag and push it
   only after maintainer approval; the release workflow builds the distribution
   and publishes the GitHub release and PyPI package.
