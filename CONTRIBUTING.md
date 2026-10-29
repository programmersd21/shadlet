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
pytest
cd packages/renderer && npm run typecheck && npm run test && npm run build
python -m mkdocs build --strict
```

## pull requests

- keep changes focused.
- add tests for new behaviour.
- update documentation.
- do not weaken type checking.

## ai code policy

- ai-assisted contributions are allowed when reviewed by a maintainer.
- contributors must understand and own any submitted code.
- do not submit unreviewed generated code.
- all changes must pass ruff, mypy, pyright, pytest, and renderer checks.
- keep changes focused and documented.
