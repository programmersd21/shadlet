# shadlet

python-first web applications with a shadcn/ui-based React renderer.

shadlet lets developers build modern applications in python while React renders the interface. The Python runtime manages state, events, routing and session isolation. The renderer provides Shadlet's documented shadcn/ui-based components.

## what shadlet provides

- a typed python component api
- session-scoped reactive state
- a versioned json protocol between python and react
- a vite-powered react renderer with tailwind css
- a starlette web runtime with websocket communication
- a polished typer and rich cli
- github project templates

## status

Shadlet 0.6.0 is a focused compatibility and developer-experience release. It
keeps protocol v2, fixes semantic HTML serialization and server-table bounds,
and includes runnable starter templates. See the [changelog](changelog.md)
and [limitations](limitations.md) for the verified scope and runtime boundaries.
This release does not claim complete parity with the current shadcn/ui catalogue;
see the [component catalogue](components/catalogue.md) for the supported set.

## quick links

- [getting started](getting-started/index.md)
- [installation](getting-started/installation.md)
- [first app](getting-started/first-app.md)
- [react extensions](extensions.md)
- [architecture](architecture/index.md)
- [component catalogue](components/catalogue.md)
- [runnable examples](https://github.com/programmersd21/shadlet/tree/main/examples)
