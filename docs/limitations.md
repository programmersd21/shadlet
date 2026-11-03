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
  message validation, size limits, and invalid-message recovery are covered by
  integration tests.
- **state and rendering**: state assignment, serialization failures, diff
  generation, patch bounds, and stale-update recovery are covered by tests.
- **distribution**: the wheel and source distribution include the renderer
  bundle and templates; a clean wheel install is built in CI.
- **smart port auto-switching**: automatic port collision detection
  (`find_available_port`).
- **authentic shadcn/ui**: 56 built-in components based on shadcn/ui
  `base-vega`, with Geist Variable sans and mono typography.

## not covered

- sessions are in memory and are not shared between workers or restarts.
- no built-in authentication provider; applications supply their own hook.
- no browser end-to-end (Playwright) suite in CI yet.
- no automated per-component visual regression suite yet.
- very large component trees and high concurrency have not been benchmarked
  against published targets.

## platform support

- python 3.11 and newer.
- current evergreen browsers with WebSocket support.
- maintainers need Node.js 20+ and npm to rebuild the renderer; end users do
  not.
