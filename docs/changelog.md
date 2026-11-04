# changelog

see the complete changelog at the repository root: `CHANGELOG.md`.

## 0.4.0 - unreleased

- added `PORT` support with documented port precedence and `/healthz`.
- added DataTable loading/error/retry states, accessible filters, column
  visibility, controlled row selection, superseded-query cancellation, and
  browser coverage for server-side search.
- added deployment examples, representative WCAG axe coverage, and an
  informational runtime benchmark suite.
- added extension project scaffolding and package validation commands.
- made extension discovery transactional and retained multiple pydantic
  validation messages for the same field.
- updated the renderer's protocol validator to Zod 4 and its development
  server to Vite 7.3.7 to address published dependency advisories.

## 0.3.0 - 2026-11-03

first-class runtime APIs and release verification.

- pydantic forms, server-driven tables, managed background tasks, multipart
  uploads, and query-parameter state.
- Python entry-point extensions with wheel assets and automatic React loading.
- protocol version 2, Playwright Chromium coverage, and a node-free extension
  wheel integration test.
- centralised version metadata at `0.3.0`.

## 0.2.0 - 2026-11-03

reliability, security, and protocol release.

- explicit `hello` handshake with protocol negotiation before the first render.
- token-based session restoration, ttl expiry, session limits, and per-session
  task cleanup.
- origin validation, connection authentication, message size limits, and event
  rate limits.
- shared protocol fixtures validated by pydantic and zod, plus renderer patch
  validation and resynchronization.
- renderer assets are served from `/_shadlet_assets`; project assets remain at
  `/assets`.
- centralised version metadata at `0.2.0`.

## 0.1.1 - 2026-11-02

- web-only runtime; desktop packaging, Electron, and PyInstaller were removed.
- bundled renderer assets in the Python wheel.
- hot reload debouncing, port auto-switching, and Windows UTF-8 console fixes.
