# contributing

## setup

```bash
uv venv --python 3.11
uv pip install -e '.[dev]'
cd packages/renderer && npm ci
```

## checks

```bash
ruff check .
ruff format --check .
mypy .
pyright packages/python/shadlet
pytest
cd packages/renderer && npm run lint && npm run format:check && npm run typecheck && npm run test && npm run build
python -m mkdocs build --strict
```

## pull requests

- keep changes focused.
- add tests for new behaviour.
- update documentation.
- do not weaken type checking.
- run every check locally before opening a pull request.
- pull requests must pass ruff, ruff format, mypy, pyright, pytest, the renderer checks, and the strict documentation build in ci.

## ai code policy

- ai-assisted contributions are allowed when reviewed by a maintainer.
- contributors must understand and own any submitted code.
- do not submit unreviewed generated code.
- all changes must pass ruff, mypy, pyright, pytest, and renderer checks.
- keep changes focused and documented.
