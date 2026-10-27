# limitations

status and verified matrix.

## verified

- **python suite**: ruff check, ruff format, mypy, pytest (28/28 tests passing).
- **multi-session & resilience**: multi-session state isolation, offline message backpressure queueing, reconnection replay tested.
- **smart port auto-switching**: automatic port collision detection and incrementing (`find_available_port`) for both web and electron sidecar runtimes.
- **protocol validation**: bidirectional protocol models validate on python (pydantic) and typescript (zod).
- **react renderer**: strict typescript build (`tsc --noEmit`), eslint, prettier, and vitest unit/component suite (5/5 passing).
- **authentic shadcn/ui**: 56 built-in components based on shadcn/ui `base-vega`, bundled with official Geist Variable sans & mono typography.
- **visual assets & styling**: transparent svg/png icons synced across web, renderer, and electron targets; custom smooth spring physics, motion blur, and frosted glass backdrop filters.
- **desktop native bridge**: electron main process sidecar lifecycle management and node native desktop ipc test suite verified.
- **packaging pipeline**: automated end-to-end multi-platform packaging orchestration (`tooling/packaging/package.py`) with pyinstaller sidecar and electron-forge bundling.
- **cli & templates**: typer & rich cli (`dev`, `run`, `create`, `build`, `doctor`, `info`, `clean`) and github template fetcher tested.

## remaining roadmap & e2e

- cross-platform native browser/desktop playwright e2e flows in continuous integration.
- automated per-component visual regression coverage tests.
