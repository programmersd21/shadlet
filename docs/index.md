# shadlet

python-first web applications with a genuine shadcn/ui renderer.

shadlet lets developers build modern applications in python while react renders the interface. the python runtime manages state, events, routing and session isolation. the react renderer ships a complete shadcn/ui component library based on the `base-vega` style.

## what shadlet provides

- a typed python component api
- session-scoped reactive state
- a versioned json protocol between python and react
- a vite-powered react renderer with tailwind css
- a starlette web runtime with websocket communication
- a polished typer and rich cli
- github project templates

## status

the shadlet 0.4.0 release builds on packaged react extensions, http uploads,
query-parameter state, and chromium browser coverage with server-driven table
selection and query cancellation, extension scaffolding, deployment examples,
and expanded accessibility checks. see [limitations](limitations.md) for the
verified support matrix and documented runtime boundaries.

## quick links

- [getting started](getting-started/index.md)
- [installation](getting-started/installation.md)
- [first app](getting-started/first-app.md)
- [react extensions](extensions.md)
- [architecture](architecture/index.md)
- [component catalogue](components/catalogue.md)
