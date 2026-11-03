# changelog

all notable changes to shadlet are documented here.

the format follows keep a changelog.

## [0.2.0] - 2026-11-03

### added

- explicit websocket handshake: the browser sends `hello`, the server validates it, negotiates the protocol, then sends the initial render.
- token-based session restoration so reconnecting clients keep their state, with TTL expiry and session limits.
- origin validation with configurable allowed origins, and a connection authentication hook (`App(authenticate=...)`).
- per-session event rate limiting, message size limits, and connection generation tracking.
- shared protocol fixtures validated by both pydantic and zod contract tests.
- renderer patch validation and automatic resynchronization when a patch or sequence fails.
- session manager tests covering isolation, restoration, expiry, and limits.
- dedicated security, deployment, session, and configuration documentation.

### changed

- centralised the package version; `pyproject.toml`, the runtime, the CLI, and the renderer now agree on `0.2.0`.
- the renderer is served under `/_shadlet_assets`, so project `/assets` no longer shadows bundled renderer files.
- protocol schemas no longer include desktop messages; the renderer no longer contains desktop bridge code.
- `session.refresh`, toast delivery, and navigation tasks are tracked and cancelled when a session closes.
- websocket payloads are parsed with the shared pydantic models instead of ad-hoc dictionaries.

### removed

- the `reload` server message, `desktop_request`, and `desktop_result` protocol messages.
- frozen/embedded desktop asset lookup from the web server.

### fixed

- the first render is no longer sent before the client handshake is validated.
- non-root initial routes now receive an `init` message instead of an out-of-order `navigation` message.
- state changes made while an event handler holds the session lock are no longer dropped.
- invalid, stale, duplicate, oversized, and rate-limited messages are rejected without corrupting session state.
- out-of-range insert/remove patches are rejected instead of silently splicing.

## [0.1.1] - 2026-11-02

### added

- python runtime with app lifecycle, components, state, events, and routing.
- versioned json protocol between python and react.
- react renderer with tailwind css and 56 shadcn/ui base-vega components.
- web runtime with starlette and websocket transport.
- typer and rich cli.
- github project template fetcher.
- mkdocs documentation website.
- examples: counter, todo, and dashboard.
- templates: minimal, dashboard, and landing-page.
- streamlit-tier hot reload: debounced file watcher triggering smart diff-based dom patches without a full page reload.
- top banner showing reconnection status and a reconnect button on server disconnect.
- pypi packaging readiness with embedded renderer distribution assets.

### changed

- shadlet is now a web-only framework. desktop packaging and the electron runtime were removed.
- the cli keeps `create`, `dev`, `run`, `doctor`, `info`, and `clean`.
- the renderer bundle is built by maintainers and shipped in the wheel.
- enhanced hot reload watcher debouncing to avoid redundant reloads on multi-file saves.

### removed

- electron integration and electron forge.
- pyinstaller sidecar builds and desktop packaging scripts.
- desktop-only apis, cli options, examples, and documentation.
- desktop prerequisites and automatic dependency installation.

### fixed

- windows console `UnicodeEncodeError: 'charmap'` by reconfiguring stdout and stderr streams to utf-8.
- blank screen on initial launch by ensuring renderer assets are properly built and served.
- port detection now correctly skips ports that are already in use.
- fixed reload error `spec not found for the module 'main'`.
- fixed rendering errors across all examples.
- added a `TextArea` alias for `Textarea` and handled the keyword `children` in `Card`.
- removed an unreachable duplicate exit call in the cli.
