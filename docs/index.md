# shadlet

python-first web applications with a shadcn/ui-based React renderer.

shadlet lets developers build modern applications in python while React renders the interface. The Python runtime manages state, events, routing and session isolation. The renderer provides shadlet's documented shadcn/ui-based components.

## what shadlet provides

- a typed python component api
- session-scoped reactive state
- a versioned json protocol between python and react
- a vite-powered react renderer with tailwind css
- a starlette web runtime with websocket communication
- a polished typer and rich cli
- github project templates

## status

shadlet 0.7.0 is a focused performance and verification release. It keeps
protocol v2 and source compatibility for 0.6.x applications while lazy-loading
chart, calendar/date picker, and carousel adapters. The main renderer entry
chunk fell from 1,590.49kB to 1,060.3kB minified (483.47kB to 327.9kB gzip).
See the [changelog](changelog.md), [migration guide](development/migration-0.6-to-0.7.md),
and [limitations](limitations.md) for the verified scope and runtime boundaries.
This release does not claim complete parity with the current shadcn/ui catalogue;
see the [component catalogue](components/catalogue.md) and
[compatibility matrix](components/compatibility-matrix.md) for the supported
and partial set.

## quick links

- [getting started](getting-started/index.md)
- [installation](getting-started/installation.md)
- [first app](getting-started/first-app.md)
- [react extensions](extensions.md)
- [architecture](architecture/index.md)
- [component catalogue](components/catalogue.md)
- [runnable examples](https://github.com/programmersd21/shadlet/tree/main/examples)
- [Agent Skills](guides/agent-skills.md) for coding assistants
