# cli

the shadlet cli (`shadlet`) provides project management and development server commands.

```bash
shadlet create my-app
shadlet dev
shadlet run
shadlet doctor
shadlet info
shadlet clean
```

### commands

- `shadlet create <name> [--template <template>]`: scaffolds a new application from built-in templates (`minimal`, `dashboard`, `landing-page`) or any github repo (`owner/repo`).
- `shadlet dev [--host <host>] [--port <port>] [--no-browser]`: starts the local development server with hot reload (granular diff updates without page reload) and file change debouncing.
- `shadlet run`: runs the application server using Starlette and Uvicorn.
- `shadlet doctor`: audits your environment and verifies the python runtime and renderer bundle.
- `shadlet info`: displays version information and runtime environment configuration.
- `shadlet clean`: removes build caches and compiled artifacts (`dist/`, `build/`, `.cache/`).

## assets

if an `assets/` directory exists in the project, the runtime serves it at `/assets`.
