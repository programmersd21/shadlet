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
  pagination, search, sorting, and filter query validation are covered by tests.
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
  extension component, an event update, and query-state URL synchronization in
  Chromium.
- **distribution**: the wheel and source distribution include the renderer
  bundle and templates; a clean wheel install is built in CI.
- **smart port auto-switching**: automatic port collision detection
  (`find_available_port`).
- **authentic shadcn/ui**: 56 built-in components based on shadcn/ui
  `base-vega`, with geist variable sans and mono typography.

## not covered

- sessions are in memory and are not shared between workers or restarts.
- no built-in authentication provider; applications supply their own hook.
- extension authors must build and bundle their browser entry script
  themselves; there is no extension generator or `shadlet extension` cli.
  extensions are trusted application code and are not sandboxed.
- pydantic forms do not generate controls from model metadata or track
  dirty/touched state; the application composes controls and reset behavior.
- server-driven tables do not yet include loading/error states, selection
  persistence across pages, or column visibility.
- background tasks are in-memory and process-local; there is no durable queue,
  and task state does not survive process restart.
- uploads are multipart and held in memory up to the configured per-request
  limit; shadlet does not provide durable file storage.
- query-parameter state binds one scalar parameter per state slot; applications
  define parsing and serialization for custom types.
- the browser suite covers key runtime paths, not every component or browser.
- no automated per-component visual regression suite yet.
- very large component trees and high concurrency have not been benchmarked
  against published targets.

## platform support

- python 3.11 and newer.
- current evergreen browsers with WebSocket support.
- maintainers need node.js 20+ and npm to build the renderer or extension
  bundles; end users install the built Python wheels and do not need node.
