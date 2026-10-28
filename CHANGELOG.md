# changelog

all notable changes to shadlet are documented here.

the format follows keep a changelog.

## [0.1.1] - 2026-11-01

### added

- single self-contained portable executable generation (`main.exe`) with zero companion folders or loose dependencies.
- native C# stub launcher (`Launcher.cs`) compiled with Roslyn/CSC using SHA256 checksummed `%TEMP%` extraction and direct stream execution.
- automated `.ico` resolution and executable icon embedding during desktop builds (converts `.png` via Pillow if `.ico` is absent).
- high-ratio payload compression using system `7z` (level 9) with fallback to Python `zipfile` (level 9).
- size optimization stripping redundant Chromium locale files (`locales/*.pak`) and licensing bloat from the distribution payload, saving ~50MB.

### changed

- `shadlet build` output artifact path directly points to the single standalone binary (`dist/main.exe`).
- Electron main process window icon resolution prioritizes project-level icons and falls back cleanly across `.ico`, `.png`, and `.svg`.

### fixed

- Windows subprocess execution failure (`[WinError 2] The system cannot find the file specified`) when invoking `npm` by ensuring `shell=True` on Windows.
- Windows console `UnicodeEncodeError: 'charmap'` by reconfiguring stdout/stderr streams to UTF-8.
- PyInstaller sidecar build failure caused by `distutils` exclusion alias conflicts in setuptools.
- PyInstaller build abort due to global environment Qt binding conflicts (`PyQt5` vs `PySide6`) by explicitly excluding GUI toolkits from sidecar bundle.
- Blank screen on initial launch by ensuring renderer assets are properly built and served.

## [0.1.0] - 2026-10-31

### added

- `shadlet build` accepts `--input`/`-i` and `--output`/`-o`.
- automatic `assets/` directory creation in `shadlet create`.
- automatic bundling and serving of project `assets/`.
- python runtime with app lifecycle, components, state, events, routing.
- versioned json protocol between python and react.
- react renderer with tailwind css and 56 shadcn/ui base-vega components.
- web runtime with starlette and websocket transport.
- electron desktop runtime with secure preload bridge.
- pyinstaller python sidecar.
- typer and rich cli.
- github project template fetcher.
- mkdocs documentation website.
- examples: counter, todo, dashboard, file-manager.
- templates: minimal, dashboard, landing-page.
- streamlit-tier hot reload: debounced file watcher triggering smart diff-based DOM patches without full page reload.
- top banner showing reconnection status and reconnect button on server disconnect.
- auto-prerequisite check and auto-installer for desktop and renderer targets (`prereqs.py`).
- PyPI packaging readiness with embedded renderer distribution assets.

### changed

- `shadlet build` can now be run from any subdirectory (automatically discovers repo root).
- enhanced hot reload watcher debouncing to avoid redundant reloads on multi-file saves.

### fixed

- fixed reload error `spec not found for the module 'main'`.
- fixed rendering errors across all examples (`dashboard`, `file-manager`, `todo`, `counter`).
- added `TextArea` alias for `Textarea` and handled keyword `children` in `Card`.
- removed unreachable duplicate exit call in CLI.

### removed

- none.
