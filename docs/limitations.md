# limitations

status and verified matrix.

## verified

- **python suite**: `ruff check`, `ruff format --check`, `mypy`, `pyright`, and
  the full pytest suite run in CI.
- **renderer suite**: eslint, prettier, `tsc --noEmit`, vitest, and the
  production Vite build run in CI.
- **protocol contract**: the same fixtures validate against pydantic and zod.
- **websocket lifecycle**: handshake validation, protocol negotiation, session
  restoration, session isolation, origin rejection, authentication hooks,
  strict message validation, transport and application size limits, malformed
  message rate limiting, and invalid-message recovery are covered by integration
  tests.
- **security regressions**: mixed origin wildcards are rejected, production
  render and event errors hide internal details, and icon routes restrict files
  to public asset roots.
- **ipv6 port selection**: loopback port probing is tested when ipv6 is
  available.
- **disconnected interactions**: the rendered application is inert while the
  WebSocket is disconnected; events are not replayed after reconnect.
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
- **query-parameter state**: typed URL parsing, state-to-url updates, and
  back/forward navigation are covered by websocket integration tests.
- **python extensions**: entry-point discovery, package-resource serving,
  websocket metadata, and an extracted separately packaged wheel fixture are
  tested without invoking node or npm.
- **browser end-to-end**: Playwright CI covers websocket rendering, a bundled
  extension component, an event update, query-state URL synchronization, and
  server-side table search in Chromium.
- **distribution**: the wheel and source distribution include the renderer
  bundle and templates; a clean wheel install is built in CI.
- **deployment examples**: a multi-stage Docker image and Render Blueprint are
  included and the Docker image is built in CI.
- **accessibility regression checks**: axe-core scans the table and
  representative form and feedback component families against
  WCAG 2.1 A/AA rules.
- **runtime benchmarks**: an opt-in script measures representative 10k-row
  table, 1k-node render/diff, protocol serialization, and 50-session concurrent
  event workloads.
- **smart port auto-switching**: automatic port collision detection
  (`find_available_port`).
- **authentic shadcn/ui**: 56 built-in components based on shadcn/ui
  `base-vega`, with geist variable sans and mono typography.

## known scope boundaries

These are documented product and deployment boundaries, not unimplemented
items in the 0.5.0 verification checklist. Applications that need stronger
durability, multi-worker state, or broader compatibility must provide those
capabilities outside the in-memory runtime.

- sessions are in memory and are not shared between workers or restarts.
- no built-in authentication provider; applications supply their own hook.
- extension authors need Node.js and npm to build the browser bundle. the
  `shadlet extension build` command automates installation and the Vite build,
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
- the browser suite covers key runtime paths in Chromium, Firefox, and WebKit,
  not every component or prop combination.
- there is no automated per-component visual regression suite; axe coverage is
  representative, not a guarantee for every component/prop combination.
- runtime benchmarks report local measurements; no cross-hardware latency
  service-level objectives are published or enforced.

## dependency audit notes

- `npm audit --omit=dev` reports no production dependency vulnerabilities.
- `npm audit` still reports 12 moderate findings through transitive
  `minimatch` dependencies in renderer development tooling. The non-forced
  `npm audit fix` does not resolve them; npm proposes potentially breaking
  dependency changes for a forced fix.

## platform support

- python 3.11 and newer.
- current evergreen browsers with WebSocket support.
- maintainers need node.js 24 and npm to build the renderer or extension
  bundles; end users install the built Python wheels and do not need node.
