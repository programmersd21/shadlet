---
name: debug-shadlet-apps
description: Diagnose runtime, rendering, protocol, websocket, event, state, routing, form, upload, storage, or packaging failures in Shadlet 0.6.0 applications using repository evidence and reproducible checks.
---

# Debug Shadlet applications

Find a reproducible cause before changing code or adding a fallback.

## Workflow

1. Capture the failing command, Shadlet/Python/browser versions, full first traceback, and whether the issue occurs in a clean project or only the current machine.
2. Identify the boundary: Python page/component construction, event handler, websocket/protocol, renderer, browser, extension loading, or filesystem/package assets.
3. Reproduce with the narrowest existing example or test. Inspect server logs and browser console; production client errors are intentionally generic while details belong in server logs/debug mode.
4. Check state ownership and event ordering. Session state is isolated per session; container mutation in place does not trigger updates. Async DataTable queries can be cancelled and must not suppress `CancelledError`.
5. For Windows temporary-directory failures, inspect pytest's actual `basetemp`, ACLs, and open handles. `tests/conftest.py` assigns a per-process UUID path under the system temp directory with a repository fallback. Do not delete another run's temporary directory or treat pytest teardown errors as product test failures without tracing the initial error.
6. Add a regression test at the failing boundary, fix the cause, and rerun that test followed by the suite relevant to the change.
7. Update troubleshooting docs only after confirming the diagnosed behavior.

## References

- `docs/faq.md`
- `docs/troubleshooting/index.md`
- `docs/architecture/protocol.md`
- `docs/architecture/runtime.md`
- `docs/architecture/security.md`
- `tests/conftest.py`
