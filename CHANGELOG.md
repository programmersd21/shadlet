# changelog

all notable changes to shadlet are documented here.

the format follows keep a changelog.

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
