# changelog

see the complete changelog at the repository root: `CHANGELOG.md`.

## 0.2.0 - 2026-11-03

Reliability, security, and protocol release.

- Explicit `hello` handshake with protocol negotiation before the first render.
- Token-based session restoration, TTL expiry, session limits, and per-session task cleanup.
- Origin validation, connection authentication hook, message size limits, and event rate limits.
- Shared protocol fixtures validated by pydantic and zod, plus renderer patch validation and resync.
- Renderer assets are served from `/_shadlet_assets`; project assets remain at `/assets`.
- Centralised version metadata at `0.2.0`.

## 0.1.1 - 2026-11-02

- Web-only runtime; desktop packaging, Electron, and PyInstaller were removed.
- Bundled renderer assets in the Python wheel.
- Hot reload debouncing, port auto-switching, and Windows UTF-8 console fixes.
