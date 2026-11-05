# cli

the shadlet cli (`shadlet`) provides project management and development server commands.

```bash
shadlet create my-app
shadlet dev
shadlet run
shadlet doctor
shadlet info
shadlet clean
shadlet extension create my-extension
shadlet extension build
shadlet extension check
shadlet extension info
```

### commands

- `shadlet create <name> [--template <template>] [--target <directory>] [--var KEY=VALUE]`: scaffolds a new application from built-in templates (`minimal`, `dashboard`, `landing-page`) or a github repository (`owner/repo`). `--var` may be repeated for manifest-declared text variables; private github repositories can use `GITHUB_TOKEN` or `--token`.
- `shadlet dev [--host <host>] [--port <port>] [--no-browser]`: starts the local development server with hot reload (granular diff updates without page reload) and file change debouncing.
- `shadlet run`: runs the application server using Starlette and Uvicorn.
- `shadlet doctor`: audits your environment and verifies the python runtime and renderer bundle.
- `shadlet info`: displays version information and runtime environment configuration.
- `shadlet extension create <name> [--target <directory>]`: creates a
  separately packaged React extension project with Python entry-point
  metadata, a browser bundle setup, assets, and a test.
- `shadlet extension build [<directory>] [--install/--no-install]`: installs
  browser dependencies by default, runs the project's npm build, then verifies
  the packaged assets. Node.js and npm are required.
- `shadlet extension check [<directory>]`: imports the declared extension
  factory and verifies its manifest, entry-point namespace, package version,
  wheel asset inclusion, and built asset files.
- `shadlet extension info [<directory>]`: prints manifest metadata, component
  names, asset locations, and entry/stylesheet sizes.

`check`, `build`, and `info` execute extension project code. use them only with
trusted source.

## assets

if an `assets/` directory exists in the project, the runtime serves it at `/assets`.
