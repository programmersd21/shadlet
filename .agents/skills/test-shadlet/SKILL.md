---
name: test-shadlet
description: Choose, write, and run appropriate tests for Shadlet Python runtime, React renderer, browser interactions, examples, packaging, and documentation. Use when adding or diagnosing verification.
---

# Test Shadlet

Choose tests by boundary and behavior; never rely on snapshots alone for interactive components.

## Workflow

1. Read `docs/development/testing.md` and inspect adjacent tests before adding new test helpers.
2. Python API, serialization, sessions, routes, storage, templates, and CLI: add pytest coverage under `tests/unit` or `tests/integration`.
3. React component behavior: add Vitest/Testing Library coverage in `packages/renderer`. Verify keyboard and focus for interactive primitives.
4. Browser-only behavior, websocket events, routing, extension loading, and responsive interactions: use Playwright specs in `packages/renderer/e2e`.
5. Use deterministic input, explicit viewport/browser, and stable waits. Do not make random data or wall-clock timestamps part of visual assertions.
6. For Windows pytest temp cleanup, use pytest's configured per-run base. Diagnose handles/ACLs rather than broad exception suppression. Avoid hard-coding a shared `.pytest-tmp` path.
7. Run the narrow test first, then the applicable full suite. Report exact commands, counts, skips, and failures; distinguish environment errors from assertion failures.

## Common commands

```console
pytest . -q
cd packages/renderer
npm run test
npm run test:e2e
npm run typecheck
```

## References

- `docs/development/testing.md`
- `tests/conftest.py`
- `packages/renderer/package.json`
