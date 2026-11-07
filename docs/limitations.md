# limitations

status and verified matrix for shadlet 0.8.0.

## verified

- **python suite**: `ruff check`, `ruff format --check`, `mypy`, and the full
  pytest suite run in ci. current result: 222 passed.
- **renderer suite**: eslint, prettier, `tsc --noEmit`, vitest, production vite
  build, and bundle budget checks run in ci. current result: 41 passed.
- **protocol contract**: shared fixtures validate against pydantic and zod.
- **websocket lifecycle**: handshake validation, protocol negotiation, session
  restoration, session isolation, origin rejection, authentication hooks,
  strict message validation, size limits, malformed-message rate limiting, and
  invalid-message recovery are covered by integration tests.
- **security regressions**: mixed origin wildcards are rejected, production
  render and event errors hide internal details, and icon routes restrict files
  to public asset roots.
- **ipv6 port selection**: loopback port probing is tested when ipv6 is
  available.
- **disconnected interactions**: the rendered application is inert while the
  websocket is disconnected; events are not replayed after reconnect.
- **state and rendering**: state assignment, serialization failures, diff
  generation, patch bounds, and stale-update recovery are covered by tests.
- **pydantic form submission**: `ui.pydantic_form` validates values with
  pydantic v2 and reports field and form errors through reactive state.
- **server-driven table queries**: current-page row rendering and strict
  pagination, search, sorting, filter query validation, loading/error display,
  retry state, controlled row selection, and cancellation of superseded async
  query callbacks are covered by tests.
- **session-owned tasks**: async progress state, cancellation on session close,
  and process-local ownership are available through `Context.start_task`.
- **http uploads**: multipart parsing, text fields, multiple files per field,
  application and endpoint byte limits, authentication, and origin checks are
  covered by tests.
- **query-parameter state**: typed url parsing, state-to-url updates, and
  back/forward navigation are covered by websocket integration tests.
- **python extensions**: entry-point discovery, package-resource serving,
  websocket metadata, and an extracted separately packaged wheel fixture are
  tested without invoking node or npm.
- **browser end-to-end**: playwright ci covers websocket rendering, a bundled
  extension component, an event update, query-state url synchronization, and
  server-side table search in chromium.
- **distribution**: the wheel and source distribution include the renderer
  bundle and templates; a clean wheel install is built in ci.
- **deployment examples**: a multi-stage docker image and render blueprint are
  included and the docker image is built in ci.
- **accessibility regression checks**: axe-core scans the table and
  representative form and feedback component families against
  wcag 2.1 a/aa rules.
- **runtime benchmarks**: an opt-in script measures representative 10k-row
  table, 1k-node render/diff, protocol serialization, and 50-session concurrent
  event workloads.
- **smart port auto-switching**: automatic port collision detection
  (`find_available_port`).
- **shadcn/ui-based components**: the supported component set is listed in the
  [component catalogue](components/catalogue.md) and the generated
  [compatibility matrix](components/compatibility-matrix.md); all 56 pinned
  upstream components have a python type and renderer adapter, but fidelity
  remains `partial` where the upstream component exposes richer props, events,
  keyboard behavior, or accessibility semantics. full upstream parity is not
  claimed.
- **custom fonts**: font registration, duplicate rejection, missing-file
  validation, weight ranges, italic descriptors, generated css, theme variables,
  and session initialisation are covered by python tests. only fonts marked
  `preload=True` are preloaded; remote sources are loaded by the browser and
  are not fetched by python.
- **document workspace**: the flagship example demonstrates sqlite persistence,
  68 seeded sections, kpi cards, analytics charts, tabs, server-side tables,
  dialogs, reviewer assignment, and responsive navigation.

## known scope boundaries

these are documented product and deployment boundaries. applications that need
stronger durability, multi-worker state, or broader compatibility must provide
those capabilities outside the in-memory runtime.

- sessions are in memory and are not shared between workers or restarts.
- no built-in authentication provider; applications supply their own hook.
- extension authors need node.js and npm to build the browser bundle. the
  `shadlet extension build` command automates installation and the vite build,
  then validates the packaged assets. extensions are trusted application code
  and are not sandboxed.
- pydantic forms do not generate controls from model metadata or track
  dirty/touched state; the application composes controls and reset behavior.
- server-driven table callbacks are cancelled when superseded, but cancellation
  cannot undo external side effects or work that suppresses cancellation.
- background tasks are in-memory and process-local; there is no durable queue,
  and task state does not survive process restart.
- uploads are multipart and held in memory up to the configured per-request
  limit. `LocalStorage` provides safe local-file persistence, but shadlet does
  not provide cloud, distributed, or multi-worker storage.
- query-parameter state binds one scalar parameter per state slot; applications
  define parsing and serialization for custom types.
- the browser suite covers key runtime paths in chromium, firefox, and webkit,
  not every component or prop combination.
- there is no automated per-component visual regression suite; axe coverage is
  representative, not a guarantee for every component/prop combination.
- runtime benchmarks report local measurements; no cross-hardware latency
  service-level objectives are published or enforced.
- custom fonts require browser-available urls or packaged assets; shadlet
  validates source paths but does not subset, convert, or optimize font files.
- the document workspace is an example application and does not provide
  production authentication, authorization, or multi-user persistence.

## dependency audit notes

- `npm audit --omit=dev` reports no production dependency vulnerabilities.
- `npm audit` still reports 12 moderate findings through transitive
  `minimatch` dependencies in renderer development tooling. the non-forced
  `npm audit fix` does not resolve them; npm proposes potentially breaking
  dependency changes for a forced fix.

## platform support

- python 3.11 and newer.
- current evergreen browsers with websocket support.
- maintainers need node.js 24 and npm to build the renderer or extension
  bundles; end users install the built python wheels and do not need node.
