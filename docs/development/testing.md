# testing

run the test and verification suites across python, frontend, and documentation:

```bash
# python static analysis and tests
ruff check packages/python tests
ruff format --check packages/python tests
PYTHONPATH=packages/python mypy packages/python/shadlet/
PYTHONPATH=packages/python pyright packages/python/shadlet
PYTHONPATH=packages/python pytest tests/

# react renderer lint, formatting, typecheck, vitest, and production build
cd packages/renderer
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
cd ../..

# documentation build
python -m mkdocs build --strict
```
