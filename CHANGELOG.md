# changelog

all notable changes to shadlet are documented here.

the format follows keep a changelog.

## [0.6.0] - 2026-11-05

### added

- ten maintained Agent Skills for application building, interface design, component and extension authoring, debugging, contribution, review, testing, releases, and migration, with validated host-specific mirrors.
- expanded runnable examples and a guided learning path for core framework features.
- `ui.Marker` for semantic highlighted text and `ui.CodeBlock` for copyable,
  line-numbered plain code.
- runnable settings, authentication UI demo, and CRUD demo project templates.
- a responsive landing-page template with semantic sections and working
  fragment navigation.

### changed

- Python `as_` choices for `Box`, `Grid`, and `Text` now serialize using the
  renderer's `as` prop. `Box` and `Grid` accept `id` for fragment targets.
- server-side `DataTable` page sizes are limited to the same 1–500 range as
  validated query events.
- built-in project templates now target shadlet 0.6.0.
- protocol remains version 2. This release does not claim complete shadcn/ui
  component parity.

### verification

- `.venv\\Scripts\\pytest.exe . -q`: 210 passed, including example startup and skill validation
  smoke tests. Two concurrent runs also passed.
- `npm run test -- --run`: 35 passed across 8 Vitest files.
- `npm run test:e2e`: 12 Playwright tests passed across Chromium, Firefox, and
  WebKit.
- `npm run typecheck`, `npm run lint`, and `npm run format:check`: passed.
- Ruff check and format check: passed; targeted mypy: passed for four changed
  Python modules.
- `mkdocs build --strict`: passed.
- `python -m build`: wheel and sdist built as shadlet 0.6.0. The wheel contains
  renderer assets and all built-in templates.
- `npm run build`: passed. Vite reports a 1,590.49 kB minified main chunk
  (483.47 kB gzip), above its 500 kB advisory threshold.

## [0.5.0] - 2026-11-05

### added

- complete generated Lucide icon catalogue pinned to `lucide-react` 0.577.0:
  1,951 names (1,702 unique shapes) shared by Python and the renderer, with a
  lazy-loaded browser chunk.
- `ui.icons` exposes every Lucide name as `icons.arrow_up_right(...)`,
  including aliases. `Icon`, `Button`, `MenuItem`, `TabItem`, and `SidebarItem`
  validate icon names during construction.
- `LocalStorage` provides safe relative keys, atomic and streaming writes,
  overwrite control, traversal checks, and size limits. `UploadedFile` adds
  `safe_filename` and `save_to(storage, key=...)`.
- `WebConfig` adds `max_event_payload_bytes`, `max_tree_nodes`, and
  `max_tree_depth` limits. tree limits count component and text nodes.
- extension manifests add `description`, `requires_shadlet`, and `components`
  metadata with validation. `shadlet extension build` installs dependencies,
  runs the browser build, and validates assets; `shadlet extension info` prints
  manifest and packaged-asset metadata.
- renderer component errors now recover when their subtree content changes,
  including props, events, children, and slots. loading buttons expose
  `aria-busy`.
- icon guide and a 0.4.0-to-0.5.0 migration guide.

### changed

- request paths are percent-decoded exactly once. malformed escapes, invalid
  UTF-8, encoded separators, NUL bytes, backslashes, control characters, and
  dot segments are rejected before route matching.
- invalid initial routes and navigation requests return generic client-facing
  messages in production; details remain available in debug mode and logs.
- extension project scaffolding now pins a compatible shadlet minor range and
  includes manifest metadata.
- versions are aligned at 0.5.0 across Python, the renderer package, protocol
  fixtures, templates, and documentation.
- Lucide ISC and Feather MIT notices are included in distributions.

### fixed

- pytest now creates a unique writable temporary base per process, avoiding collisions between concurrent Windows runs and falling back to a repository-local unique directory when the system temp directory is unavailable.
- route parameters are no longer decoded twice.
- unknown icons fail explicitly instead of rendering an unrelated fallback.
- storage rejects Windows drive/alternate-stream syntax, trailing dots/spaces,
  and symlink escapes in addition to POSIX traversal.

### verification

- Python: Ruff lint and formatting, mypy, and Pyright passed; all 176 pytest
  tests passed.
- renderer: ESLint, Prettier, and TypeScript checks passed; all 29 Vitest tests
  passed; the production build succeeded.
- browser: all 12 Playwright tests passed across Chromium, Firefox, and WebKit,
  including icons, component recovery, extension loading, DataTable search, and
  representative WCAG 2.1 A/AA axe checks.
- documentation: strict MkDocs build passed.
- extension smoke: `extension create` followed by the real `extension build`
  installed dependencies, built assets, and passed validation with no npm audit
  vulnerabilities.
- packaging: wheel and source distribution built at 0.5.0; wheel contents
  included the renderer bundle, icon data, storage module, templates, and
  third-party notices. a clean Python 3.11 wheel install rendered an app and
  reported `renderer ready` without Node.js.

## [0.4.0] - 2026-11-04

### added

- `GET /healthz` provides a minimal liveness response without exposing runtime
  state.
- `app.run()` supports the platform-standard `PORT` environment variable.
- `ui.DataTable` adds reactive loading and error states, retry callbacks,
  accessible per-column text filters, column visibility, controlled row
  selection, superseded async query cancellation, sort announcements, and
  responsive horizontal scrolling.
- `Select`, `NativeSelect`, `RadioGroup`, `Combobox`, and `InputOTP` accept
  explicit accessible names; a representative WCAG axe suite checks built-in
  form, feedback, and table component families.
- multi-stage Docker and Render deployment examples include a non-root runtime
  and health check; opt-in runtime benchmarks report measured local results.
- `shadlet extension create` scaffolds a separately packaged Python and React
  extension; `shadlet extension check` validates its manifest and assets.
- regression coverage for browser-driven server-side table search, runtime
  environment ports, extension scaffolding, and extension discovery failures.

### changed

- port precedence is now `SHADLET_PORT`, then `PORT`, then the explicit
  `app.run(port=...)` value; invalid values fail with a clear error.
- failed extension discovery no longer leaves previously loaded extensions
  partially registered, and successful discovery remains idempotent.
- pydantic form errors sharing a field path are preserved together rather than
  silently overwriting one another.
- updated the renderer's protocol validator to Zod 4 and its development
  server to Vite 7.3.7 to address published dependency advisories.

### fixed

- server-side DataTable search now dispatches the changed query to Python.
- closed sessions reject new background tasks without leaving task state marked
  as running.

### verification

- Python: Ruff lint and formatting, mypy, and Pyright passed; all 145 pytest
  tests passed.
- renderer: ESLint, Prettier, and TypeScript checks passed; all 27 Vitest tests
  and all 3 Playwright tests passed; the production build succeeded.
- documentation: strict MkDocs build passed.
- packaging: wheel and source distribution built, and the wheel's renderer
  bundle and built-in templates were verified; an isolated wheel install
  smoke test passed.
- dependencies: `npm audit --omit=dev` reported no production vulnerabilities.
- Docker: the deployment example is built by main-branch CI; a local Docker
  image build was not run.

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
