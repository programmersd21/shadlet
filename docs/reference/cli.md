# cli

The shadlet CLI (`shadlet`) provides project management, development servers, and production compilation tools.

```bash
shadlet create my-app
shadlet dev
shadlet dev --desktop
shadlet run
shadlet build
shadlet build --input app.py --output myapp
shadlet doctor
shadlet info
shadlet clean
```

### Commands

- `shadlet create <name> [--template <template>]`: Scaffolds a new application from built-in templates (`minimal`, `dashboard`, `landing-page`) or any GitHub repo (`owner/repo`).
- `shadlet dev [--desktop] [--host <host>] [--port <port>] [--no-browser]`: Starts the local development server with Streamlit-tier hot reload (granular diff updates without page reload) and file change debouncing. With `--desktop`, launches the application inside Electron.
- `shadlet run`: Runs the application server in production mode using Starlette and Uvicorn.
- `shadlet build [-i <input>] [-o <output>]`: Packages the full standalone native Electron desktop application with the bundled Python sidecar runtime. Automatically verifies all desktop prerequisites, compiles the React renderer, and outputs ready-to-run desktop packages in `dist/`. Custom logos and window titles are dynamically embedded, and native window menus are disabled for a clean desktop feel.
- `shadlet doctor`: Audits your environment, verifying Python, Node.js, npm, PyInstaller, Electron, and the renderer bundle.
- `shadlet info`: Displays version information and runtime environment configuration.
- `shadlet clean`: Removes build caches, packaging outputs, and compiled artifacts (`dist/`, `build/`, `.cache/`).


## assets

if an `assets/` directory exists in the project, `shadlet build` bundles it and the runtime serves it at `/assets`.
