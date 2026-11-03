# changelog

all notable changes to shadlet are documented here.

the format follows keep a changelog.

## [0.3.0] - 2026-11-03

### added

- `ui.pydantic_form` validates model-backed submissions and publishes field and
  form errors through reactive state.
- `ui.DataTable` supports server-side pagination, sorting, search, and validated
  filters for large result sets.
- `Context.start_task` and `Context.task_state` provide session-owned async
  workers with reactive progress, completion, failure, and cancellation state.
- `App.upload` provides bounded multipart http upload endpoints with fields,
  multiple files, origin checks, and optional application authentication.
- `Context.query_state` binds typed reactive state to browser query parameters
  and supports back/forward navigation.
- python extension entry-point discovery, package-resource asset serving, and
  automatic namespaced react component loading are supported.
- Playwright browser coverage and a node-free separately packaged extension
  wheel integration test run in CI.

### changed

- advanced the client/server wire protocol to version 2 for extension metadata
  and query-state url updates.
- aligned application, renderer, template, and package metadata at `0.3.0`.
- updated the README, guides, configuration reference, and support matrix for
  the 0.3.0 runtime.

### fixed

- applied declared template variables, enforced minimum shadlet versions, and
  rejected unsupported manifest fields instead of silently ignoring them.
- rejected mixed wildcard origins, restricted icon and extension assets to
  declared public roots, and hid production exception details.
- aligned TypeScript protocol validation with python's strict extra-field
  handling and enforced the websocket transport frame limit.
- gated renderer interactions while disconnected and added IPv6 port probing.

## [0.2.0] - 2026-11-03

### added

- explicit websocket handshake: the browser sends `hello`, the server validates
  it, negotiates the protocol, then sends the initial render.
- token-based session restoration so reconnecting clients keep their state,
  with ttl expiry and session limits.
- origin validation with configurable allowed origins and a connection
  authentication hook (`App(authenticate=...)`).
- per-session event rate limiting, message size limits, and connection
  generation tracking.
- shared protocol fixtures validated by both pydantic and zod contract tests.
- renderer patch validation and automatic resynchronization when a patch or
  sequence fails.
- session manager tests covering isolation, restoration, expiry, and limits.
- security, deployment, session, and configuration documentation.

### changed

- centralised the package version; `pyproject.toml`, the runtime, the cli, and
  the renderer agree on `0.2.0`.
- served renderer assets under `/_shadlet_assets` so project `/assets` no
  longer shadows bundled renderer files.
- removed desktop messages and bridge code from the web protocol and renderer.
- tracked session refresh, toast delivery, and navigation tasks for cleanup.

### removed

- the `reload`, `desktop_request`, and `desktop_result` protocol messages.
- frozen/embedded desktop asset lookup from the web server.

### fixed

- sent `init` after handshake validation, including for non-root initial paths.
- preserved state changes made during event handlers and rejected stale,
  duplicate, oversized, and rate-limited messages.
- rejected out-of-range insert/remove patches instead of silently splicing.

## [0.1.1] - 2026-11-02

### added

- Python runtime with app lifecycle, components, state, events, and routing.
- versioned json protocol between Python and React.
- React renderer with tailwind css and 56 shadcn/ui base-vega components.
- web runtime with Starlette and WebSocket transport.
- typer and rich cli, github project templates, and MkDocs documentation.
- counter, todo, and dashboard examples plus minimal, dashboard, and landing
  page templates.
- bundled renderer assets in the Python wheel.

### changed

- made shadlet a web-only framework and removed desktop packaging.
- kept the renderer build in maintainer workflows; end users run with Python.
- debounced hot reload to avoid redundant updates on multi-file saves.

### fixed

- fixed Windows console encoding, blank startup pages, port collisions, and
  rendering issues across examples.
