# testing

run the test and verification suites across python, frontend, electron ipc, and documentation:

```bash
# python static analysis & tests (28 tests)
ruff check packages/python tests
ruff format --check packages/python tests
PYTHONPATH=packages/python mypy packages/python/shadlet/ --ignore-missing-imports
PYTHONPATH=packages/python pytest tests/

# react renderer lint, formatting, typecheck, vitest (5 tests), and production build
cd packages/renderer
npm run lint
npm run format:check
npm run typecheck
npm run test
npm run build
cd ../..

# electron desktop native ipc bridge suite
node --test packages/electron/test/desktop-ipc.test.js

# documentation build
python -m mkdocs build --strict
```
